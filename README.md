# 🧠 Antigravity AI Agent Telegram Bot

Kendalikan seluruh server, pengerjaan kodingan, debugging, dan proyek pengembangan kamu secara langsung melalui chat Telegram dengan kecerdasan AI Antigravity.

---

## 🌟 Fitur Utama
- 🤖 **Kendalikan Antigravity AI dari Telegram**: Kirim instruksi kodingan, perbaikan bug, atau buat project baru dari mana saja via HP/Laptop.
- 💬 **Sesi Percakapan Berkelanjutan**: Mengingat riwayat percakapan secara otomatis (Gunakan `/new` untuk mulai dari awal).
- 📂 **Flexible Workspace**: Ubah lokasi kerja AI di server secara dinamis dengan `/workspace /path/tujuan`.
- 📊 **Monitoring Server**: Cek beban CPU, RAM, Disk, dan status executable `agy`.
- 🔒 **Sistem Keamanan Strict**: Hanya akun Telegram milikmu (`ALLOWED_USER_IDS`) yang dapat mengendalikan server.

---

## 🚀 Panduan Penggunaan Perintah
| Perintah | Deskripsi |
|---|---|
| `/start` atau `/help` | Menampilkan menu bantuan utama |
| `/new` atau `/reset` | Memulai sesi obrolan AI baru dari awal |
| `/workspace [path]` | Mengubah direktori kerja AI di server |
| `/status` | Cek status RAM, Disk, CPU & lokasi `agy` |

---

## 🏃 Menjalankan Service 24 Jam

Disiapkan sebagai Service Systemd Linux:
```bash
systemctl status antigravity-bot
systemctl restart antigravity-bot
```
