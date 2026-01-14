import json
import os
from config import DPI

from ocr.pdf_loader import pdf_to_images
from ocr.image_preprocessor import preprocess_image
from ocr.word_blocks import extract_word_blocks
from ocr.line_blocks import group_words_into_lines
from ocr.section_blocks import build_section_blocks
from ocr.table_blocks import extract_tables, build_table_blocks
from ocr.block_factory import create_block
from ocr.readable_formatter import save_readable_output

# ✅ NEW IMPORT (this is the missing piece)
from ocr.form_parser import build_form_blocks


PDF_PATH = "data/main_test_file.pdf"


def run_ocr(pdf_path):
    pages = pdf_to_images(pdf_path, dpi=DPI)
    all_blocks = []

    for page in pages:
        page_num = page["page_number"]
        image = preprocess_image(page["image"])

        page_block = create_block("PAGE", Page=page_num)
        all_blocks.append(page_block)

        word_blocks = extract_word_blocks(image, page_num)
        line_blocks = group_words_into_lines(word_blocks)

        # ✅ NEW: Build form fields + key-value pairs + checkboxes
        form_blocks = build_form_blocks(line_blocks, word_blocks)

        section_blocks = build_section_blocks(line_blocks)

        table_lines = extract_tables(line_blocks)
        table_blocks = build_table_blocks(table_lines)

        # ✅ Best order for readable_formatter output
        all_blocks.extend(section_blocks)
        all_blocks.extend(form_blocks)   # ✅ IMPORTANT
        all_blocks.extend(table_blocks)
        all_blocks.extend(line_blocks)
        all_blocks.extend(word_blocks)

    result = {
        "DocumentMetadata": {
            "Pages": len(pages)
        },
        "Blocks": all_blocks
    }

    # Save JSON output
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "output_blocks.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=4)

    print(f"✅ Saved JSON to: {output_path}")

    # ✅ Save readable outputs (TXT + structured JSON)
    save_readable_output(all_blocks, output_path)

    return result


if __name__ == "__main__":
    run_ocr(PDF_PATH)