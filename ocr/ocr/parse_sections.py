import re

def is_heading(line):
    return (
        line.isupper()
        and len(line.split()) <= 5
        and not re.search(r"[.:]", line)
    )

def parse_sections(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    sections = []
    current_section = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect heading
        if is_heading(line):
            if current_section:
                sections.append(current_section)

            current_section = {
                "title": line,
                "type": None,
                "content": []
            }
            i += 1
            continue

        if not current_section:
            i += 1
            continue

        # Bullet list
        if line.startswith("-"):
            current_section["type"] = "bullets"
            current_section["content"].append(line[1:].strip())
            i += 1
            continue

        # Numbered list
        if re.match(r"\d+\.", line):
            current_section["type"] = "numbered"
            current_section["content"].append(line.split(".", 1)[1].strip())
            i += 1
            continue

        # Key-value pairs
        if ":" in line and len(line.split(":")[0].split()) <= 3:
            current_section["type"] = "key_value"
            key, val = line.split(":", 1)
            current_section["content"].append({
                key.strip(): val.strip()
            })
            i += 1
            continue

        # Table header (simple heuristic)
        if current_section["type"] is None and len(line.split()) > 3:
            current_section["type"] = "paragraph"

        # Paragraph
        current_section["content"].append(line)
        i += 1

    if current_section:
        sections.append(current_section)

    return sections
