# 🧠 Antigravity AI Agent Telegram Bot Engine

Control your Linux server, coding execution, bug fixes, and development workflows remotely via Telegram powered by Google Antigravity AI CLI (gy).

## 🌟 Key Features

- **🤖 Remote AI Coding Agent**: Execute complex coding tasks, refactoring, and multi-file debugging directly from Telegram.
- **▶️ Seamless Session Resumption**: Resume conversation sessions (/resume) without cluttering chat context.
- **📱 Persistent Quick Menu**: Interactive bottom keyboard buttons (💬 Active Session, ▶️ Resume / Session, 🔄 New Session, 📂 Workspace, 📊 System & Usage, ❓ Help).
- **📂 Interactive Workspace Picker**: Switch server working directories instantly via 1-tap inline buttons.
- **📊 Realtime Token & System Health**: Monitor token consumption, RAM usage, CPU load, and disk metrics.
- **🛡️ Authorized Security**: Strict access control matching pre-configured Telegram User IDs via environment variables.

## 🛠️ Tech Stack

- **Python 3.12** / pyTelegramBotAPI (	elebot)
- **Antigravity CLI** (gy) Integration & Stream Runner
- **python-dotenv** (Environment Management)
- **Systemd Service** (24/7 Automated Linux Background Runner)

## 🚀 Quick Setup

1. **Clone Repository**:
   `ash
   git clone https://github.com/daffaroffi/telegram-antigravity-bot.git
   cd telegram-antigravity-bot
   `

2. **Configure Environment Variables**:
   Copy .env.example to .env:
   `ash
   cp .env.example .env
   `
   Edit .env:
   `env
   TELEGRAM_BOT_TOKEN= your_bot_token_here
   ALLOWED_USER_IDS=8927082329
   AGY_PATH=/root/.local/bin/agy
   DEFAULT_WORKSPACE=/root/my-project
   `

3. **Install Dependencies & Run**:
   `ash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python bot.py
   `

---
***REMOVED***
