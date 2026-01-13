import pytesseract
from pytesseract import Output

'''def extract_text_blocks(image, lang="eng"):
    data = pytesseract.image_to_data(
        image,
        lang=lang,
        output_type=Output.DICT
    )

    blocks = []
    n = len(data["text"])

    for i in range(n):
        text = data["text"][i].strip()
        if not text:
            continue

        block = {
            "block_id": f"b{i}",
            "text": text,
            "confidence": float(data["conf"][i]),
            "bbox": [
                data["left"][i],
                data["top"][i],
                data["left"][i] + data["width"][i],
                data["top"][i] + data["height"][i]
            ]
        }
        blocks.append(block)

    full_text = " ".join([b["text"] for b in blocks])

    return full_text, blocks


import pytesseract
from pytesseract import Output

def extract_words(image, lang="eng"):
    data = pytesseract.image_to_data(
        image,
        lang=lang,
        output_type=Output.DICT
    )

    words = []
    n = len(data["text"])

    for i in range(n):
        text = data["text"][i].strip()
        if not text:
            continue

        words.append({
            "text": text,
            "conf": float(data["conf"][i]),
            "x": data["left"][i],
            "y": data["top"][i],
            "w": data["width"][i],
            "h": data["height"][i]
        })

    return words'''

import pytesseract

def extract_full_text(image, lang="eng"):
    return pytesseract.image_to_string(image, lang=lang)
