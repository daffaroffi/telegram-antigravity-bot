import subprocess
import os
import json
import re
import time
import threading
from datetime import datetime
import config

active_conversations = {}
chat_token_usage = {}  # chat_id -> {'session_tokens': 0, 'total_tokens': 0}


def get_token_usage(chat_id: int):
    if chat_id not in chat_token_usage:
        chat_token_usage[chat_id] = {'session_tokens': 0, 'total_tokens': 0}
    return chat_token_usage[chat_id]


def get_recent_sessions(limit=5):
    """Scans brain directory for recent Antigravity conversation sessions"""
    brain_dir = "/root/.gemini/antigravity-cli/brain"
    if not os.path.exists(brain_dir):
        return []

    sessions = []
    try:
        entries = [os.path.join(brain_dir, d) for d in os.listdir(brain_dir) if os.path.isdir(os.path.join(brain_dir, d))]
        entries.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        for folder in entries[:limit]:
            conv_id = os.path.basename(folder)
            transcript_file = os.path.join(folder, ".system_generated", "logs", "transcript.jsonl")
            
            title = "Sesi Percakapan"
            date_str = ""

            if os.path.exists(transcript_file):
                try:
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            data = json.loads(line)
                            if data.get("type") == "USER_INPUT":
                                content = data.get("content", "")
                                match = re.search(r'<USER_REQUEST>(.*?)</USER_REQUEST>', content, re.DOTALL)
                                if match:
                                    raw_text = match.group(1).strip()
                                    title = raw_text[:50] + ("..." if len(raw_text) > 50 else "")
                                else:
                                    title = content[:50] + ("..." if len(content) > 50 else "")
                                
                                created_at = data.get("created_at", "")
                                if created_at:
                                    try:
                                        dt = datetime.strptime(created_at[:19], "%Y-%m-%dT%H:%M:%S")
                                        date_str = dt.strftime("%d %b %H:%M")
                                    except Exception:
                                        date_str = created_at[:10]
                                break
                except Exception:
                    pass

            if not date_str:
                mtime = os.path.getmtime(folder)
                date_str = datetime.fromtimestamp(mtime).strftime("%d %b %H:%M")

            sessions.append({
                "id": conv_id,
                "title": title,
                "date": date_str
            })
    except Exception as e:
        print(f"[ERROR] Failed to list sessions: {e}")

    return sessions


def get_session_transcript_preview(conv_id: str, max_turns: int = 3) -> str:
    """Reads transcript.jsonl for conv_id and formats previous turns into clean Markdown text"""
    transcript_file = os.path.join("/root/.gemini/antigravity-cli/brain", conv_id, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(transcript_file):
        return "📜 <i>(Riwayat percakapan tidak dapat ditemukan)</i>"

    turns = []
    current_turn = {"user": "", "ai": ""}

    try:
        with open(transcript_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg_type = data.get("type")
                    
                    if msg_type == "USER_INPUT":
                        content = data.get("content", "")
                        match = re.search(r'<USER_REQUEST>(.*?)</USER_REQUEST>', content, re.DOTALL)
                        raw_user = match.group(1).strip() if match else content.strip()
                        
                        if current_turn["user"] or current_turn["ai"]:
                            turns.append(current_turn)
                            current_turn = {"user": "", "ai": ""}
                        current_turn["user"] = raw_user

                    elif msg_type == "PLANNER_RESPONSE":
                        content = data.get("content", "")
                        if content:
                            current_turn["ai"] = content.strip()
                except Exception:
                    pass

        if current_turn["user"] or current_turn["ai"]:
            turns.append(current_turn)

        if not turns:
            return "📜 <i>(Sesi ini belum memiliki percakapan)</i>"

        recent_turns = turns[-max_turns:]
        formatted = []
        for turn in recent_turns:
            u_text = turn["user"][:250] + ("..." if len(turn["user"]) > 250 else "")
            a_text = turn["ai"][:250] + ("..." if len(turn["ai"]) > 250 else "")

            u_clean = u_text.replace("<", "&lt;").replace(">", "&gt;")
            a_clean = a_text.replace("<", "&lt;").replace(">", "&gt;")

            entry = f"👤 <b>User:</b>\n<i>{u_clean}</i>\n\n🤖 <b>Antigravity AI:</b>\n<i>{a_clean}</i>"
            formatted.append(entry)

        header = f"📜 <b>Pratinjau Percakapan Sebelumnya:</b>\n\n"
        body = "\n\n───────────────\n\n".join(formatted)
        return header + body

    except Exception as e:
        return f"📜 Error membaca riwayat: {str(e)}"


def run_antigravity_stream(prompt: str, chat_id: int, workspace_dir: str, progress_callback=None) -> tuple:
    """Runs agy with stream-json, feeding real-time updates and returning (response, usage_dict)"""
    if not os.path.exists(config.AGY_PATH):
        return f"❌ Executable agy tidak ditemukan di <code>{config.AGY_PATH}</code>", {}

    cwd = workspace_dir or config.DEFAULT_WORKSPACE
    os.makedirs(cwd, exist_ok=True)

    cmd = [
        config.AGY_PATH,
        "-p", prompt,
        "--output-format", "stream-json",
        "--dangerously-skip-permissions"
    ]

    conv_target = active_conversations.get(chat_id)
    if isinstance(conv_target, str):
        cmd.extend(["--conversation", conv_target])
    elif conv_target is True:
        cmd.append("-c")

    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        final_response = ""
        last_update_time = 0
        current_activities = []
        turn_usage = {}

        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                event_type = data.get("event")

                if event_type == "init":
                    conv_id = data.get("conversation_id")
                    if conv_id:
                        active_conversations[chat_id] = conv_id

                elif event_type == "step_update":
                    step = data.get("step_update", {})
                    step_type = step.get("step_type", "")
                    
                    # Extract usage if present in step
                    if step.get("usage"):
                        turn_usage = step.get("usage")

                    tool_call = step.get("tool_call") or step.get("tool") or {}
                    tool_name = tool_call.get("name", step_type)
                    args = tool_call.get("args", {})
                    
                    action = args.get("toolAction") or args.get("toolSummary")
                    if action:
                        current_activities.append(f"• 🛠️ {action}")
                    elif tool_name and tool_name not in ["unknown", "user_input", "checkpoint"]:
                        current_activities.append(f"• ⚡ Processing step: <code>{tool_name}</code>")

                    now = time.time()
                    if progress_callback and (now - last_update_time >= 1.5) and current_activities:
                        recent_logs = "\n".join(current_activities[-5:])
                        progress_callback(f"⚡ <b>Antigravity AI sedang bekerja...</b>\n\n🔄 <b>Aktivitas Real-Time:</b>\n{recent_logs}")
                        last_update_time = now

                elif event_type == "result":
                    res = data.get("result", {})
                    final_response = res.get("response", "")
                    if res.get("usage"):
                        turn_usage = res.get("usage")

            except json.JSONDecodeError:
                pass

        process.stdout.close()
        process.wait()

        if not active_conversations.get(chat_id):
            active_conversations[chat_id] = True

        # Accumulate token usage stats
        usage_stats = get_token_usage(chat_id)
        if turn_usage and turn_usage.get("total_tokens"):
            t_tok = turn_usage["total_tokens"]
            usage_stats['session_tokens'] += t_tok
            usage_stats['total_tokens'] += t_tok

        resp_text = final_response if final_response else "✅ Tugas selesai."
        return resp_text, turn_usage

    except Exception as e:
        return f"❌ <b>Gagal menjalankan Antigravity:</b> {str(e)}", {}


def run_smash_stream(prompt: str, chat_id: int, workspace_dir: str, progress_callback=None) -> tuple:
    smash_prompt = (
        "💥 SMASH MODE INSTRUCTION: Complete the following task with maximum effort, thoroughness, and speed. "
        "Fix all bugs, resolve any broken code/tests, build the project, and do not stop until everything runs 100% cleanly:\n\n"
        f"{prompt}"
    )
    return run_antigravity_stream(smash_prompt, chat_id, workspace_dir, progress_callback)


def resume_stream(prompt: str, chat_id: int, workspace_dir: str, progress_callback=None) -> tuple:
    resume_prompt = prompt if prompt else "Lanjutkan pekerjaan dan konteks dari poin terakhir yang belum selesai."
    return run_antigravity_stream(resume_prompt, chat_id, workspace_dir, progress_callback)


def set_active_session(chat_id: int, conv_id: str):
    active_conversations[chat_id] = conv_id
    # Reset session tokens counter for new/selected session
    get_token_usage(chat_id)['session_tokens'] = 0


def reset_session(chat_id: int):
    active_conversations.pop(chat_id, None)
    get_token_usage(chat_id)['session_tokens'] = 0
