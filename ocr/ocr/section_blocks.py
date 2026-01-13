import re
from ocr.block_factory import create_block

def is_heading(line):
    text = line["Text"].strip()
    return (
        text.isupper()
        and len(text.split()) <= 5
        and re.match(r"[A-Z\s]+$", text)
    )

def build_section_blocks(line_blocks):
    sections = []
    current_section = None

    for line in line_blocks:
        if is_heading(line):
            if current_section:
                sections.append(current_section)

            current_section = create_block(
                "SECTION",
                Title=line["Text"],
                Page=line.get("Page", 1),  # FIX: Add Page attribute
                Relationships=[{
                    "Type": "CHILD",
                    "Ids": []
                }]
            )
            continue

        if current_section:
            current_section["Relationships"][0]["Ids"].append(line["Id"])

    if current_section:
        sections.append(current_section)

    return sections