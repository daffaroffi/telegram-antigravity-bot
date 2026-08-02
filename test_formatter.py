from formatter import markdown_to_telegram_html

sample_markdown = """
# Judul Utama Project
Berikut adalah penjelasan singkat mengenai **fitur rich text** di Telegram.

## Kode Python Contoh:
```python
def hitung(a, b):
    # Mengembalikan hasil penjumlahan
    return a + b
```

> Ini adalah kutipan penjelasan panjang yang bisa di-expand (collapsible blockquote) di Telegram chat!
> Sangat rapi dan tidak memenuhi layar.

### Fitur Lainnya:
* Penggunaan `inline code` untuk nama variabel.
* Format *italic* dan **bold** otomatis.
"""

result = markdown_to_telegram_html(sample_markdown)
print("=== RESULT TELEGRAM HTML ===")
print(result)
