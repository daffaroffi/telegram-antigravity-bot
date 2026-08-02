import re
import html

def markdown_to_telegram_html(text: str) -> str:
    """
    Converts standard Markdown text to Telegram-compliant HTML.
    Safely escapes HTML special characters (<, >, &) outside of generated tags.
    """
    if not text:
        return ""

    code_blocks = []
    inline_codes = []

    # 1. Extract Code Blocks (```lang ... ```)
    def save_code_block(match):
        lang = match.group(1) or ""
        code = match.group(2)
        escaped_code = html.escape(code)
        idx = len(code_blocks)
        if lang:
            tag = f'<pre><code class="language-{html.escape(lang.strip())}">{escaped_code}</code></pre>'
        else:
            tag = f'<pre>{escaped_code}</pre>'
        code_blocks.append(tag)
        return f"XCBPHX{idx}XCBPHX"

    # Match ```lang\ncode``` or ```code```
    pattern_code_block = re.compile(r'```([a-zA-Z0-9_\-+]*)\n?(.*?)```', re.DOTALL)
    text = pattern_code_block.sub(save_code_block, text)

    # 2. Extract Inline Code (`code`)
    def save_inline_code(match):
        code = match.group(1)
        escaped_code = html.escape(code)
        idx = len(inline_codes)
        tag = f'<code>{escaped_code}</code>'
        inline_codes.append(tag)
        return f"XICPHX{idx}XICPHX"

    pattern_inline_code = re.compile(r'`([^`\n]+)`')
    text = pattern_inline_code.sub(save_inline_code, text)

    # 3. HTML Escape the remaining plain text
    text = html.escape(text)

    # 4. Links: [text](url)
    def convert_link(match):
        label = match.group(1)
        url = match.group(2)
        return f'<a href="{url}">{label}</a>'

    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', convert_link, text)

    # 5. Process lines (Headers, Blockquotes, Lists, HR)
    lines = text.split('\n')
    formatted_lines = []
    quote_buffer = []

    def flush_quote():
        nonlocal quote_buffer, formatted_lines
        if quote_buffer:
            quote_text = "\n".join(quote_buffer)
            if len(quote_text) > 200:
                formatted_lines.append(f'<blockquote expandable>{quote_text}</blockquote>')
            else:
                formatted_lines.append(f'<blockquote>{quote_text}</blockquote>')
            quote_buffer = []

    for line in lines:
        stripped = line.strip()
        
        # Check blockquotes (&gt; text because html.escape escaped > to &gt;)
        if stripped.startswith('&gt; '):
            quote_content = line.replace('&gt; ', '', 1)
            quote_buffer.append(quote_content)
            continue
        elif stripped == '&gt;':
            quote_buffer.append("")
            continue
        else:
            flush_quote()

        # Check Headers
        if re.match(r'^#\s+(.*)$', line):
            line = re.sub(r'^#\s+(.*)$', r'<b>📌 \1</b>', line)
        elif re.match(r'^##\s+(.*)$', line):
            line = re.sub(r'^##\s+(.*)$', r'<b>🔷 \1</b>', line)
        elif re.match(r'^###+\s+(.*)$', line):
            line = re.sub(r'^###+\s+(.*)$', r'<b>🔹 \1</b>', line)

        # Check Horizontal Rule
        elif re.match(r'^[\-\*\_]{3,}$', stripped):
            line = '───────────────'

        # Check Unordered List Bullet (- or * or +)
        elif re.match(r'^[\-\*\+]\s+(.*)$', line):
            line = re.sub(r'^[\-\*\+]\s+(.*)$', r'• \1', line)

        formatted_lines.append(line)

    flush_quote()
    text = '\n'.join(formatted_lines)

    # 6. Bold (**text** or __text__)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text, flags=re.DOTALL)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text, flags=re.DOTALL)

    # 7. Italic (*text* or _text_)
    text = re.sub(r'(?<![a-zA-Z0-9])\*(.*?)\*(?![a-zA-Z0-9])', r'<i>\1</i>', text, flags=re.DOTALL)
    text = re.sub(r'(?<![a-zA-Z0-9])_(.*?)_(?![a-zA-Z0-9])', r'<i>\1</i>', text, flags=re.DOTALL)

    # 8. Strikethrough (~~text~~)
    text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text, flags=re.DOTALL)

    # 9. Restore Inline Code & Code Blocks
    for i, tag in enumerate(inline_codes):
        text = text.replace(f"XICPHX{i}XICPHX", tag)

    for i, tag in enumerate(code_blocks):
        text = text.replace(f"XCBPHX{i}XCBPHX", tag)

    return text


def split_telegram_html(text: str, max_length: int = 4000) -> list:
    """
    Splits long HTML text into chunks <= max_length characters without breaking HTML tags.
    Maintains open tags across chunk boundaries.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""
    open_tags = []

    # Tag regex pattern
    tag_pattern = re.compile(r'</?([a-zA-Z0-9\-]+)[^>]*>')

    lines = text.split('\n')

    for line in lines:
        # If adding this line exceeds max_length
        if len(current_chunk) + len(line) + 1 > max_length - 50:
            if current_chunk:
                # Close all open tags for current chunk
                closed_chunk = current_chunk
                for tag in reversed(open_tags):
                    closed_chunk += f'</{tag}>'
                chunks.append(closed_chunk)

                # Start new chunk with re-opened tags
                current_chunk = "".join([f'<{tag}>' for tag in open_tags])
            
        current_chunk += (line + '\n')

        # Update open_tags state
        for match in tag_pattern.finditer(line):
            full_tag = match.group(0)
            tag_name = match.group(1).lower()
            if full_tag.startswith('</'):
                if tag_name in open_tags:
                    for idx in range(len(open_tags) - 1, -1, -1):
                        if open_tags[idx] == tag_name:
                            open_tags.pop(idx)
                            break
            elif not full_tag.endswith('/>'):
                # Ignore self-closing tags
                open_tags.append(tag_name)

    if current_chunk.strip():
        # Close any remaining open tags
        for tag in reversed(open_tags):
            current_chunk += f'</{tag}>'
        chunks.append(current_chunk)

    return chunks if chunks else [text]
