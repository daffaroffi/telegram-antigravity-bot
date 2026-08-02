import os
import sys
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_USERS_RAW = os.getenv("ALLOWED_USER_IDS", "").strip()

ALLOWED_USER_IDS = []
if ALLOWED_USERS_RAW:
    for uid in ALLOWED_USERS_RAW.split(","):
        uid_clean = uid.strip()
        if uid_clean.isdigit():
            ALLOWED_USER_IDS.append(int(uid_clean))

AGY_PATH = os.getenv("AGY_PATH", "/root/.local/bin/agy").strip()
DEFAULT_WORKSPACE = os.getenv("DEFAULT_WORKSPACE", "/root/my-project").strip()

os.makedirs(DEFAULT_WORKSPACE, exist_ok=True)


def validate_config():
    errors = []
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        errors.append("TELEGRAM_BOT_TOKEN is not set in .env")

    if errors:
        print("[ERROR] Configuration validation failed:")
        for err in errors:
            print(f"  - {err}")
        return False

    if not ALLOWED_USER_IDS:
        print("[WARNING] ALLOWED_USER_IDS is empty in .env. Bot will report Telegram ID to user on first /start.")
    return True
