import pytesseract
from pytesseract import Output
from ocr.block_factory import create_block

def extract_word_blocks(image, page_num):
    data = pytesseract.image_to_data(image, output_type=Output.DICT)
    blocks = []

    h, w = image.shape[:2]

    for i, text in enumerate(data["text"]):
        if not text.strip():
            continue

        block = create_block(
            "WORD",
            Text=text.strip(),
            Confidence=float(data["conf"][i]),
            Page=page_num,
            Geometry={
                "BoundingBox": {
                    "Left": data["left"][i] / w,
                    "Top": data["top"][i] / h,
                    "Width": data["width"][i] / w,
                    "Height": data["height"][i] / h
                }
            }
        )
        blocks.append(block)

    return blocks