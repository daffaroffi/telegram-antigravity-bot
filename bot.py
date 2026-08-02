import os
import sys
import functools
import traceback
import threading
import time
import psutil
import telebot
from telebot import types

import config
import agent_runner

if not config.validate_config():
    print("Please configure .env before starting the bot.")
    sys.exit(1)

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")
current_workspace = config.DEFAULT_WORKSPACE


def register_telegram_commands():
    """Registers slash commands into Telegram UI menu so typing '/' brings up autocomplete"""
    commands = [
        types.BotCommand("start", "Tampilkan menu utama & panduan"),
        types.BotCommand("sessions", "📜 Lihat & pilih riwayat sesi percakapan"),
        types.BotCommand("resume", "▶️ Pilih/lanjutkan sesi percakapan AI"),
        types.BotCommand("smash", "💥 Mode Hantam Bug & Force Fix sampai tuntas!"),
        types.BotCommand("new", "🔄 Reset & mulai sesi AI baru"),
        types.BotCommand("goal", "🎯 Eksekusi tugas / goal khusus hingga tuntas"),
        types.BotCommand("plan", "📋 Mode perencanaan (Plan Mode)"),
        types.BotCommand("workspace", "📂 Lihat/ubah folder kerja di server"),
        types.BotCommand("status", "📊 Cek statistik CPU, RAM, Disk & AI"),
        types.BotCommand("help", "❓ Tampilkan daftar lengkap perintah")
    ]
    try:
        bot.set_my_commands(commands)
        print("✅ Telegram Slash Commands registered successfully!")
    except Exception as e:
        print(f"[WARNING] Gagal mendaftarkan slash commands ke Telegram: {e}")


register_telegram_commands()


def reply_safe(message, text, **kwargs):
    """Safely reply to a message, falling back to send_message if original message was deleted"""
    try:
        return bot.reply_to(message, text, **kwargs)
    except Exception:
        try:
            return bot.send_message(message.chat.id, text, **kwargs)
        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")
            return None


def is_authorized(user_id: int) -> bool:
    if not config.ALLOWED_USER_IDS:
        return False
    return user_id in config.ALLOWED_USER_IDS


def check_auth(func):
    """Decorator to enforce security for message handlers"""
    @functools.wraps(func)
    def wrapper(message, *args, **kwargs):
        user_id = message.from_user.id
        if not config.ALLOWED_USER_IDS:
            reply_safe(
                message,
                f"👋 <b>Selamat Datang di Antigravity AI Bot!</b>\n\n"
                f"ID Telegram Anda adalah: <code>{user_id}</code>\n\n"
                f"⚠️ <b>Bot belum dikonfigurasi dengan ID Anda.</b>\n"
                f"Silakan buka file <code>.env</code> di server dan tambahkan:\n"
                f"<code>ALLOWED_USER_IDS={user_id}</code>\n\n"
                f"Setelah itu restart bot."
            )
            return
        if not is_authorized(user_id):
            reply_safe(
                message,
                f"⛔ <b>Akses Ditolak!</b>\nID Telegram Anda ({user_id}) tidak terdaftar dalam ALLOWED_USER_IDS di <code>.env</code>."
            )
            print(f"[SECURITY ALERT] Unauthorized access attempt from User ID: {user_id}")
            return
        return func(message, *args, **kwargs)
    return wrapper


def check_auth_callback(func):
    """Decorator to enforce security for callback queries (button clicks)"""
    @functools.wraps(func)
    def wrapper(call, *args, **kwargs):
        user_id = call.from_user.id
        if not is_authorized(user_id):
            bot.answer_callback_query(call.id, "⛔ Akses ditolak! ID Anda tidak terdaftar.", show_alert=True)
            return
        return func(call, *args, **kwargs)
    return wrapper


def send_long_message(chat_id, text):
    """Splits and sends messages that exceed Telegram's 4096 character limit"""
    max_length = 4000
    if len(text) <= max_length:
        try:
            bot.send_message(chat_id, text, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, text, parse_mode=None)
        return

    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    for chunk in chunks:
        try:
            bot.send_message(chat_id, chunk, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, chunk, parse_mode=None)


def keep_typing_alive(chat_id, stop_event):
    """Sends 'typing' chat action every 4 seconds to maintain Telegram UI status"""
    while not stop_event.is_set():
        try:
            bot.send_chat_action(chat_id, 'typing')
        except Exception:
            pass
        time.sleep(4)


@bot.message_handler(commands=['start', 'help'])
@check_auth
def send_welcome(message):
    help_text = (
        "🧠 <b>Antigravity AI Agent Bot</b>\n\n"
        "Selamat datang! Kamu memiliki akses penuh ke Antigravity AI dari Telegram.\n\n"
        "<b>Perintah Slash Keren:</b>\n"
        "📜 <code>/sessions</code> - Lihat & pilih riwayat sesi percakapan\n"
        "▶️ <code>/resume [instruksi]</code> - Pilih atau lanjutkan sesi percakapan terakhir\n"
        "💥 <code>/smash <deskripsi></code> - Mode Hantam Bug & Force Fix sampai tuntas!\n"
        "🔄 <code>/new</code> - Reset & mulai sesi obrolan baru\n"
        "🎯 <code>/goal <deskripsi></code> - Eksekusi tugas / goal khusus\n"
        "📋 <code>/plan <deskripsi></code> - Aktifkan mode perencanaan (Plan Mode)\n"
        "📂 <code>/workspace [path]</code> - Ubah direktori kerja AI\n"
        "📊 <code>/status</code> - Cek status RAM, Disk & AI\n"
        "❓ <code>/help</code> - Tampilkan bantuan ini\n\n"
        f"<b>Workspace Saat Ini:</b>\n<code>{current_workspace}</code>\n\n"
        "💡 <i>Ketik pesan atau instruksi kodingan apa saja. AI akan membaca, mengedit, dan mengeksekusi perintah di server!</i>"
    )
    reply_safe(message, help_text)


@bot.message_handler(commands=['sessions'])
@check_auth
def list_sessions_command(message):
    show_session_picker(message)


@bot.message_handler(commands=['resume'])
@check_auth
def execute_resume(message):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        resume_prompt = args[1].strip()
        status_text = "▶️ <b>RESUME MODE!</b>\n🔄 <i>Melanjutkan sesi percakapan dari konteks terakhir...</i>"
        process_custom_agent_prompt(message, resume_prompt, status_text, runner_func=agent_runner.resume_session)
    else:
        show_session_picker(message)


def show_session_picker(message):
    sessions = agent_runner.get_recent_sessions(limit=5)
    if not sessions:
        reply_safe(message, "📜 Belum ada riwayat sesi percakapan di server.")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for sess in sessions:
        btn_text = f"💬 {sess['title']} ({sess['date']})"
        btn = types.InlineKeyboardButton(btn_text, callback_data=f"select_session|{sess['id']}")
        markup.add(btn)

    btn_new = types.InlineKeyboardButton("🔄 Sesi Baru (/new)", callback_data="select_session|new")
    markup.add(btn_new)

    text = (
        "📜 <b>Pilih Sesi Percakapan Antigravity:</b>\n\n"
        "Klik salah satu sesi di bawah untuk memilih dan melanjutkan percakapan dari riwayat tersebut:"
    )
    reply_safe(message, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_session|"))
@check_auth_callback
def handle_session_selection(call):
    conv_id = call.data.split("|", 1)[1]
    if conv_id == "new":
        agent_runner.reset_session(call.message.chat.id)
        bot.answer_callback_query(call.id, "Memulai sesi baru.")
        bot.edit_message_text(
            "🔄 <b>Sesi Percakapan Baru Dimulai.</b>\nSiap menerima instruksi baru!",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        agent_runner.set_active_session(call.message.chat.id, conv_id)
        bot.answer_callback_query(call.id, "Sesi dipilih.")
        bot.edit_message_text(
            f"✅ <b>Sesi Percakapan Diaktifkan!</b>\n"
            f"🆔 <b>ID Sesi:</b> <code>{conv_id}</code>\n\n"
            f"Pesan kamu selanjutnya akan melanjutkan sesi percakapan ini.",
            call.message.chat.id,
            call.message.message_id
        )


@bot.message_handler(commands=['smash'])
@check_auth
def execute_smash(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        reply_safe(message, "💥 <b>SMASH MODE!</b>\nMasukkan deskripsi bug atau tugas yang mau di-smash.\nContoh: <code>/smash Perbaiki semua error di bot.py dan tes sampai jalan!</code>")
        return

    smash_prompt = args[1].strip()
    status_text = "💥 <b>SMASH MODE ACTIVATED!</b>\n🔨 <i>AI sedang menghancurkan bug dan mengeksekusi perbaikan secara tuntas...</i>"
    process_custom_agent_prompt(message, smash_prompt, status_text, runner_func=agent_runner.run_smash_mode)


@bot.message_handler(commands=['new', 'reset'])
@check_auth
def reset_conversation(message):
    agent_runner.reset_session(message.chat.id)
    reply_safe(message, "🔄 <b>Sesi obrolan Antigravity AI berhasil di-reset.</b>\nSiap untuk instruksi baru!")


@bot.message_handler(commands=['goal'])
@check_auth
def execute_goal(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        reply_safe(message, "⚠️ Masukkan deskripsi goal.\nContoh: <code>/goal Buat fitur autentikasi JWT lengkap di project-a</code>")
        return

    goal_prompt = f"Goal: {args[1].strip()}. Pastikan tugas ini diselesaikan sepenuhnya secara tuntas."
    process_agent_prompt(message, goal_prompt)


@bot.message_handler(commands=['plan'])
@check_auth
def execute_plan(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        reply_safe(message, "⚠️ Masukkan topik perencanaan.\nContoh: <code>/plan Rencana arsitektur database untuk e-commerce</code>")
        return

    plan_prompt = f"Buat rencana langkah demi langkah (Plan) untuk: {args[1].strip()}"
    process_agent_prompt(message, plan_prompt)


@bot.message_handler(commands=['workspace'])
@check_auth
def change_workspace(message):
    global current_workspace
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        reply_safe(message, f"📂 Workspace saat ini:\n<code>{current_workspace}</code>\n\nGunakan: <code>/workspace /path/tujuan</code>")
        return

    new_ws = os.path.abspath(args[1].strip())
    if not os.path.exists(new_ws):
        os.makedirs(new_ws, exist_ok=True)

    current_workspace = new_ws
    reply_safe(message, f"✅ Workspace AI diubah ke:\n<code>{current_workspace}</code>")


@bot.message_handler(commands=['status'])
@check_auth
def send_status(message):
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status_text = (
            "📊 <b>Status Server & AI Engine</b>\n\n"
            f"💻 <b>CPU Usage:</b> {cpu_usage}%\n"
            f"🧠 <b>RAM Usage:</b> {ram.percent}% ({ram.used // (1024**2)} MB / {ram.total // (1024**2)} MB)\n"
            f"💾 <b>Disk Usage:</b> {disk.percent}% ({disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB)\n"
            f"🚀 <b>AGY Path:</b> <code>{config.AGY_PATH}</code>\n"
            f"📂 <b>Workspace:</b> <code>{current_workspace}</code>"
        )
        reply_safe(message, status_text)
    except Exception as e:
        reply_safe(message, f"❌ Error status: {str(e)}")


@bot.message_handler(func=lambda msg: True, content_types=['text'])
@check_auth
def handle_text_prompt(message):
    prompt = message.text.strip()
    if not prompt:
        return
    process_agent_prompt(message, prompt)


def process_agent_prompt(message, prompt):
    status_text = "⚡ <b>Antigravity AI sedang berpikir & bekerja di server...</b>"
    process_custom_agent_prompt(message, prompt, status_text, runner_func=agent_runner.run_antigravity_agent)


def process_custom_agent_prompt(message, prompt, status_text, runner_func):
    status_msg = reply_safe(message, status_text)

    stop_typing = threading.Event()
    typing_thread = threading.Thread(target=keep_typing_alive, args=(message.chat.id, stop_typing))
    typing_thread.start()

    try:
        response = runner_func(prompt, message.chat.id, current_workspace)
        
        stop_typing.set()
        typing_thread.join(timeout=1)

        if status_msg:
            try:
                bot.delete_message(message.chat.id, status_msg.message_id)
            except Exception:
                pass

        send_long_message(message.chat.id, response)

    except Exception as e:
        stop_typing.set()
        traceback.print_exc()
        reply_safe(message, f"❌ <b>Error memproses prompt:</b> {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting Antigravity AI Agent Telegram Bot with Session Selection...")
    print(f"📂 Default Workspace Dir: {config.DEFAULT_WORKSPACE}")
    print(f"🔒 Allowed User IDs: {config.ALLOWED_USER_IDS}")
    print("🤖 Bot is polling for messages...")
    bot.infinity_polling(timeout=20, long_polling_timeout=20)
