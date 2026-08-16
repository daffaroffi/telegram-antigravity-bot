# Antigravity AI Agent Telegram Bot Engine

[English](README.md) | [Bahasa Indonesia](README-id.md)

---

Kendalikan server Linux, eksekusi kode, perbaikan bug, dan alur kerja pengembangan Anda dari jarak jauh melalui Telegram, didukung oleh CLI AI Google Antigravity (`agy`).

## Fitur Utama

- **Agen Coding AI Jarak Jauh**: Eksekusi tugas coding kompleks, refactoring, dan debugging multi-file langsung dari Telegram.
- **Lanjutkan Sesi dengan Mulus**: Lanjutkan sesi percakapan (/resume) tanpa mengacaukan konteks chat.
- **Menu Cepat Persisten**: Tombol keyboard bawah yang interaktif (Active Session, Resume / Session, New Session, Workspace, System & Usage, Help).
- **Pemilih Workspace Interaktif**: Ganti direktori kerja server secara instan melalui tombol inline satu-tap.
- **Kesehatan Token & Sistem Real-time**: Pantau konsumsi token, penggunaan RAM, beban CPU, dan metrik disk.
- **Keamanan Terotorisasi**: Kontrol akses ketat yang mencocokkan User ID Telegram yang telah dikonfigurasi melalui variabel lingkungan.

## Tech Stack

- **Python 3.12** / pyTelegramBotAPI (telebot)
- **Integrasi CLI Antigravity** (`agy`) & Stream Runner
- **python-dotenv** (Manajemen Lingkungan)
- **Systemd Service** (Runner Latar Belakang Linux 24/7 Otomatis)

## Setup Cepat

1. **Clone Repository**:
   ```bash
   git clone https://github.com/daffaroffi/telegram-antigravity-bot.git
   cd telegram-antigravity-bot
   ```

2. **Konfigurasi Variabel Lingkungan**:
   Salin .env.example ke .env:
   ```bash
   cp .env.example .env
   ```
   Edit .env:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ALLOWED_USER_IDS=8927082329
   AGY_PATH=/root/.local/bin/agy
   DEFAULT_WORKSPACE=/root/my-project
   ```

3. **Instal Dependensi & Jalankan**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python bot.py
   ```

---

***REMOVED***

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
