import os
import sys
import functools
import traceback
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


def send_long_message(chat_id, text):
    """Splits and sends messages that exceed Telegram's 4096 character limit"""
    max_length = 4000
    if len(text) <= max_length:
        try:
            bot.send_message(chat_id, text, parse_mode="HTML")
        except Exception:
            # Fallback to plain text if HTML parsing fails
            bot.send_message(chat_id, text, parse_mode=None)
        return

    # Split text into chunks
    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    for chunk in chunks:
        try:
            bot.send_message(chat_id, chunk, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, chunk, parse_mode=None)


@bot.message_handler(commands=['start', 'help'])
@check_auth
def send_welcome(message):
    help_text = (
        "🧠 <b>Antigravity AI Agent Bot</b>\n\n"
        "Selamat datang! Kamu bisa mengendalikan AI Antigravity langsung dari Telegram.\n\n"
        "<b>Perintah Tersedia:</b>\n"
        "🆕 <code>/new</code> atau <code>/reset</code> - Mulai sesi obrolan AI baru\n"
        "📂 <code>/workspace [path]</code> - Ubah direktori kerja AI di server\n"
        "📊 <code>/status</code> - Cek status RAM, Disk & CPU server\n"
        "❓ <code>/help</code> - Tampilkan bantuan ini\n\n"
        f"<b>Workspace Saat Ini:</b>\n<code>{current_workspace}</code>\n\n"
        "💡 <i>Ketik pesan atau instruksi kodingan apa saja di sini. AI akan membaca, mengedit, dan mengeksekusi perintah di server!</i>"
    )
    reply_safe(message, help_text)


@bot.message_handler(commands=['new', 'reset'])
@check_auth
def reset_conversation(message):
    agent_runner.reset_session(message.chat.id)
    reply_safe(message, "🔄 <b>Sesi obrolan Antigravity AI berhasil di-reset.</b>\nSiap untuk instruksi baru!")


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
            f"🚀 <b>AGY Executable:</b> <code>{config.AGY_PATH}</code>\n"
            f"📂 <b>Active Workspace:</b> <code>{current_workspace}</code>"
        )
        reply_safe(message, status_text)
    except Exception as e:
        reply_safe(message, f"❌ Error status: {str(e)}")


@bot.message_handler(func=lambda msg: True, content_types=['text'])
@check_auth
def handle_agent_prompt(message):
    prompt = message.text.strip()
    if not prompt:
        return

    # Inform user that Antigravity AI is working
    status_msg = reply_safe(message, "⚡ <b>Antigravity AI sedang berpikir & bekerja di server...</b>")

    try:
        response = agent_runner.run_antigravity_agent(prompt, message.chat.id, current_workspace)
        
        # Delete temporary status message if possible
        if status_msg:
            try:
                bot.delete_message(message.chat.id, status_msg.message_id)
            except Exception:
                pass

        send_long_message(message.chat.id, response)

    except Exception as e:
        traceback.print_exc()
        reply_safe(message, f"❌ <b>Error memproses prompt:</b> {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting Antigravity AI Agent Telegram Bot...")
    print(f"📂 Default Workspace Dir: {config.DEFAULT_WORKSPACE}")
    print(f"🔒 Allowed User IDs: {config.ALLOWED_USER_IDS}")
    print("🤖 Bot is polling for messages...")
    bot.infinity_polling(timeout=20, long_polling_timeout=20)
