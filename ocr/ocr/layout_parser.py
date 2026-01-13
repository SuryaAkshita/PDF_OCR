def group_words_into_rows(words, y_threshold=15):
    rows = []

    for word in sorted(words, key=lambda w: w["y"]):
        placed = False

        for row in rows:
            if abs(row[0]["y"] - word["y"]) < y_threshold:
                row.append(word)
                placed = True
                break

        if not placed:
            rows.append([word])

    # sort words left → right inside rows
    for row in rows:
        row.sort(key=lambda w: w["x"])

    return rows