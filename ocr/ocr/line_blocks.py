from ocr.block_factory import create_block

def group_words_into_lines(word_blocks, y_threshold=0.015):
    lines = []

    # Sort words top → bottom
    sorted_words = sorted(
        word_blocks,
        key=lambda w: w["Geometry"]["BoundingBox"]["Top"]
    )

    for word in sorted_words:
        placed = False
        word_top = word["Geometry"]["BoundingBox"]["Top"]

        for line in lines:
            line_top = line["words"][0]["Geometry"]["BoundingBox"]["Top"]

            if abs(line_top - word_top) < y_threshold:
                line["words"].append(word)
                placed = True
                break

        if not placed:
            lines.append({
                "words": [word]
            })

    line_blocks = []

    for line in lines:
        words = line["words"]

        # Sort words left → right
        words.sort(
            key=lambda w: w["Geometry"]["BoundingBox"]["Left"]
        )

        text = " ".join(w["Text"] for w in words)

        left = min(w["Geometry"]["BoundingBox"]["Left"] for w in words)
        top = min(w["Geometry"]["BoundingBox"]["Top"] for w in words)
        right = max(
            w["Geometry"]["BoundingBox"]["Left"] +
            w["Geometry"]["BoundingBox"]["Width"]
            for w in words
        )
        bottom = max(
            w["Geometry"]["BoundingBox"]["Top"] +
            w["Geometry"]["BoundingBox"]["Height"]
            for w in words
        )

        # FIX: Get page number from first word
        page_num = words[0].get("Page", 1)

        line_block = create_block(
            "LINE",
            Text=text,
            Confidence=sum(w["Confidence"] for w in words) / len(words),
            Page=page_num,  # FIX: Add Page attribute
            Geometry={
                "BoundingBox": {
                    "Left": left,
                    "Top": top,
                    "Width": right - left,
                    "Height": bottom - top
                }
            },
            Relationships=[{
                "Type": "CHILD",
                "Ids": [w["Id"] for w in words]
            }]
        )

        line_blocks.append(line_block)

    return line_blocks