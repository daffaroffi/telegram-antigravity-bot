import subprocess
import os
import sys
import config

active_conversations = {}


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

    # If active conversation exists for this chat, append -c to continue
    if active_conversations.get(chat_id):
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
    """Resumes the active conversation thread with continuation flag"""
    active_conversations[chat_id] = True
    resume_prompt = prompt if prompt else "Lanjutkan pekerjaan dan konteks dari poin terakhir yang belum selesai."
    return run_antigravity_agent(resume_prompt, chat_id, workspace_dir)


def reset_session(chat_id: int):
    active_conversations.pop(chat_id, None)
