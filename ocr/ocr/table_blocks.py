import re
from ocr.block_factory import create_block

def looks_like_table_row(line):
    words = line["Text"].split()
    numeric_count = sum(
        bool(re.search(r"\d", w)) for w in words
    )
    return len(words) >= 3 and numeric_count >= 1

def extract_tables(line_blocks):
    tables = []
    current_rows = []

    for line in line_blocks:
        if looks_like_table_row(line):
            current_rows.append(line)
        else:
            if len(current_rows) >= 2:
                tables.append(current_rows)
            current_rows = []

    if len(current_rows) >= 2:
        tables.append(current_rows)

    return tables

def build_table_blocks(table_lines):
    table_blocks = []

    for table in table_lines:
        if not table:  # Safety check
            continue
            
        # FIX: Get page number from first row
        page_num = table[0].get("Page", 1)
        
        table_block = create_block(
            "TABLE",
            Page=page_num,  # FIX: Add Page attribute
            Relationships=[{
                "Type": "CHILD",
                "Ids": []
            }]
        )

        header_words = table[0]["Text"].split()

        for row_index, line in enumerate(table[1:], start=1):
            values = line["Text"].split()

            for col_index, value in enumerate(values):
                cell_block = create_block(
                    "CELL",
                    RowIndex=row_index,
                    ColumnIndex=col_index + 1,
                    Text=value,
                    Page=page_num,  # FIX: Add Page attribute
                    Relationships=[{
                        "Type": "CHILD",
                        "Ids": []
                    }]
                )

                table_block["Relationships"][0]["Ids"].append(cell_block["Id"])
                table_blocks.append(cell_block)

        table_blocks.append(table_block)

    return table_blocks