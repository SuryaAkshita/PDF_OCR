def extract_table(rows):
    header = [w["text"] for w in rows[0]]
    table = []

    for row in rows[1:]:
        values = [w["text"] for w in row]
        record = {}

        for i in range(min(len(header), len(values))):
            record[header[i]] = values[i]

        if record:
            table.append(record)

    return table