import subprocess
import os
import sys
import json
import re
from datetime import datetime
import config

active_conversations = {}


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


def run_antigravity_agent(prompt: str, chat_id: int, workspace_dir: str = None) -> str:
    """Executes Antigravity CLI with prompt and returns the response."""
    if not os.path.exists(config.AGY_PATH):
        return f"❌ Executable agy tidak ditemukan di <code>{config.AGY_PATH}</code>"

    cwd = workspace_dir or config.DEFAULT_WORKSPACE
    os.makedirs(cwd, exist_ok=True)

    cmd = [
        config.AGY_PATH,
        "-p", prompt,
        "--dangerously-skip-permissions"
    ]

    conv_target = active_conversations.get(chat_id)
    if isinstance(conv_target, str):
        cmd.extend(["--conversation", conv_target])
    elif conv_target is True:
        cmd.append("-c")

    try:
        process = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )

        # Retain current conversation state
        if not conv_target:
            active_conversations[chat_id] = True

        stdout = process.stdout.strip()
        stderr = process.stderr.strip()

        if process.returncode != 0:
            error_msg = stderr or stdout or "Unknown error"
            return f"⚠️ <b>Antigravity Error (code {process.returncode}):</b>\n<pre>{error_msg}</pre>"

        return stdout if stdout else "✅ Tugas selesai."

    except subprocess.TimeoutExpired:
        return "⏱️ <b>Timeout:</b> Waktu eksekusi Antigravity melebihi 5 menit."
    except Exception as e:
        return f"❌ <b>Gagal menjalankan Antigravity:</b> {str(e)}"


def run_smash_mode(prompt: str, chat_id: int, workspace_dir: str = None) -> str:
    """Executes Antigravity in SMASH mode (aggressive force-fix & build)"""
    smash_prompt = (
        "💥 SMASH MODE INSTRUCTION: Complete the following task with maximum effort, thoroughness, and speed. "
        "Fix all bugs, resolve any broken code/tests, build the project, and do not stop until everything runs 100% cleanly:\n\n"
        f"{prompt}"
    )
    return run_antigravity_agent(smash_prompt, chat_id, workspace_dir)


def resume_session(prompt: str, chat_id: int, workspace_dir: str = None) -> str:
    """Resumes the active conversation thread"""
    resume_prompt = prompt if prompt else "Lanjutkan pekerjaan dan konteks dari poin terakhir yang belum selesai."
    return run_antigravity_agent(resume_prompt, chat_id, workspace_dir)


def set_active_session(chat_id: int, conv_id: str):
    """Sets specific conversation ID for chat_id"""
    active_conversations[chat_id] = conv_id


def reset_session(chat_id: int):
    active_conversations.pop(chat_id, None)
