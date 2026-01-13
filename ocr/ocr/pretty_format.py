import json


def get_lines_in_reading_order(blocks, page_number):
    """
    Extract LINE blocks for a page and return their text
    in top-to-bottom, left-to-right order.
    """
    lines = [
        b for b in blocks
        if b.get("BlockType") == "LINE" and b.get("Page") == page_number
    ]

    lines.sort(
        key=lambda l: (
            l["Geometry"]["BoundingBox"]["Top"],
            l["Geometry"]["BoundingBox"]["Left"]
        )
    )

    # IMPORTANT: return only text
    return [l["Text"] for l in lines]


def lines_to_sections(lines):
    """
    Convert ordered lines into Textract-like sections
    using heading detection.
    """
    sections = []
    current = None

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        is_heading = (
            stripped.upper() == stripped and
            len(stripped.split()) <= 5 and
            len(stripped) >= 4
        )

        if is_heading:
            if current:
                sections.append(current)

            current = {
                "title": stripped,
                "content": []
            }
        else:
            if current:
                cleaned = stripped.lstrip("0123456789.- ").strip()
                if cleaned:
                    current["content"].append(cleaned)

    if current:
        sections.append(current)

    return sections


def pretty_print(blocks, page_number):
    """
    Produce clean, presentation-ready structured output
    """
    lines = get_lines_in_reading_order(blocks, page_number)
    sections = lines_to_sections(lines)

    pretty = {
        "page": page_number,
        "sections": sections
    }

    print(json.dumps(pretty, indent=4))
    return pretty