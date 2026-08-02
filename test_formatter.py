from formatter import markdown_to_telegram_html, split_telegram_html

def test_edge_cases():
    test_cases = [
        # Edge case 1: Multiple links
        "Check [Google](https://google.com) and [GitHub](https://github.com)",
        # Edge case 2: Raw code with HTML tags
        "```html\n<div class='main'>Content & 'quotes'</div>\n```",
        # Edge case 3: Mixed formatting
        "**Bold** with `inline_code` and *italic* and ~~strike~~ in one line",
        # Edge case 4: Long expandable blockquote
        "> " + "This is a very long blockquote sentence. " * 10,
        # Edge case 5: Unclosed code block
        "Text before\n```python\nprint('hello')\n```\nText after"
    ]

    for idx, tc in enumerate(test_cases, 1):
        print(f"=== TEST CASE {idx} ===")
        out = markdown_to_telegram_html(tc)
        print(out)
        chunks = split_telegram_html(out, max_length=150)
        print(f"Chunks: {len(chunks)}")
        print()

if __name__ == "__main__":
    test_edge_cases()
