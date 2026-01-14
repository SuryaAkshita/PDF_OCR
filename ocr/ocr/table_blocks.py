import re
from ocr.block_factory import create_block

def looks_like_table_row(line):
    """Enhanced table row detection"""
    words = line["Text"].split()
    
    # Check 1: Multiple words with numbers
    numeric_count = sum(bool(re.search(r"\d", w)) for w in words)
    if len(words) >= 3 and numeric_count >= 1:
        return True
    
    # Check 2: Multiple columns separated by spaces (3+ groups)
    if len(words) >= 3 and len(set(words)) == len(words):
        return True
    
    # Check 3: Contains pipe separators |
    if '|' in line["Text"]:
        return True
    
    # Check 4: Form table pattern (Date | Provider | Description)
    form_table_keywords = ['date', 'provider', 'diagnosis', 'service', 'amount', 'currency']
    text_lower = line["Text"].lower()
    keyword_matches = sum(1 for kw in form_table_keywords if kw in text_lower)
    if keyword_matches >= 2:
        return True
    
    return False

def looks_like_table_header(line):
    """Detect table headers"""
    text = line["Text"].strip()
    text_lower = text.lower()
    
    # Common header keywords
    header_keywords = [
        'name', 'date', 'number', 'address', 'amount', 'total',
        'description', 'service', 'provider', 'diagnosis', 'currency',
        'country', 'charged', 'policy', 'account'
    ]
    
    # Check if line contains multiple header keywords
    keyword_count = sum(1 for kw in header_keywords if kw in text_lower)
    
    return keyword_count >= 2

def extract_tables(line_blocks):
    """Enhanced table extraction with header detection"""
    tables = []
    current_rows = []
    has_header = False

    for i, line in enumerate(line_blocks):
        # Check if it's a header row
        if looks_like_table_header(line):
            # If we have accumulated rows, save them as a table
            if len(current_rows) >= 2:
                tables.append(current_rows)
            
            # Start new table with header
            current_rows = [line]
            has_header = True
            continue
        
        # Check if it's a regular table row
        if looks_like_table_row(line):
            current_rows.append(line)
        else:
            # End of table
            if len(current_rows) >= 2:
                tables.append(current_rows)
            current_rows = []
            has_header = False

    # Don't forget the last table
    if len(current_rows) >= 2:
        tables.append(current_rows)

    return tables

def parse_table_cells(row_text):
    """
    Smart parsing of table row into cells
    Handles pipe-separated, tab-separated, and multi-space separated
    """
    # Method 1: Pipe separated (highest priority)
    if '|' in row_text:
        return [cell.strip() for cell in row_text.split('|') if cell.strip()]
    
    # Method 2: Tab separated
    if '\t' in row_text:
        return [cell.strip() for cell in row_text.split('\t') if cell.strip()]
    
    # Method 3: Multiple spaces (3+)
    cells = re.split(r'\s{3,}', row_text)
    cells = [cell.strip() for cell in cells if cell.strip()]
    
    if len(cells) > 1:
        return cells
    
    # Method 4: Split on specific patterns for forms
    # Example: "01/15/2024 Hospital Visit $500" -> ["01/15/2024", "Hospital", "Visit", "$500"]
    # Look for dates, currency, numbers as delimiters
    
    # If we can't split intelligently, return the whole text as one cell
    return [row_text.strip()] if row_text.strip() else []


def build_table_blocks(table_lines):
    """Enhanced table block builder with intelligent cell parsing"""
    table_blocks = []

    for table in table_lines:
        if not table:
            continue
            
        page_num = table[0].get("Page", 1)
        
        # Parse all rows to determine max column count
        all_parsed_rows = []
        max_cols = 0
        
        for line in table:
            cells = parse_table_cells(line["Text"])
            all_parsed_rows.append(cells)
            max_cols = max(max_cols, len(cells))
        
        # Ensure minimum columns
        max_cols = max(max_cols, 2)
        
        table_block = create_block(
            "TABLE",
            Page=page_num,
            RowCount=len(table),
            ColumnCount=max_cols,
            Relationships=[{
                "Type": "CHILD",
                "Ids": []
            }]
        )

        # Process all rows with parsed cells
        for row_index, (line, cells) in enumerate(zip(table, all_parsed_rows)):
            # Pad cells to match max column count
            while len(cells) < max_cols:
                cells.append("")
            
            # Create cell blocks for each cell
            for col_index, cell_text in enumerate(cells[:max_cols]):
                cell_block = create_block(
                    "CELL",
                    RowIndex=row_index,
                    ColumnIndex=col_index + 1,
                    Text=cell_text,
                    Page=page_num,
                    IsHeader=(row_index == 0),  # Mark first row as header
                    ColumnSpan=1,
                    RowSpan=1,
                    Confidence=line.get("Confidence", 0),
                    Geometry=line.get("Geometry", {}),
                    Relationships=[{
                        "Type": "CHILD",
                        "Ids": []
                    }]
                )

                table_block["Relationships"][0]["Ids"].append(cell_block["Id"])
                table_blocks.append(cell_block)

        table_blocks.append(table_block)

    return table_blocks