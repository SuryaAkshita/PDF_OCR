import json


def format_readable_output(blocks, page_number):
    """Enhanced formatter with form field support"""
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append(f"PAGE {page_number}")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    # Get different block types for this page
    sections = [b for b in blocks 
                if b.get("BlockType") == "SECTION" 
                and b.get("Page") == page_number]
    
    form_fields = [b for b in blocks 
                   if b.get("BlockType") == "FORM_FIELD" 
                   and b.get("Page") == page_number]
    
    kv_pairs = [b for b in blocks 
                if b.get("BlockType") == "KEY_VALUE_SET" 
                and b.get("Page") == page_number]
    
    checkboxes = [b for b in blocks 
                  if b.get("BlockType") == "CHECKBOX" 
                  and b.get("Page") == page_number]
    
    lines = [b for b in blocks if b.get("BlockType") == "LINE"]
    line_dict = {l["Id"]: l for l in lines}
    
    tables = [b for b in blocks 
              if b.get("BlockType") == "TABLE" 
              and b.get("Page") == page_number]
    
    # Display form fields WITH VALUES
    if form_fields:
        output_lines.append("FORM FIELDS")
        output_lines.append("-" * 80)
        filled_count = 0
        empty_count = 0
        
        for field in form_fields:
            label = field.get("Label", "")
            value = field.get("Value", "")
            has_value = field.get("HasValue", False)
            
            if has_value and value:
                output_lines.append(f"  ✓ {label} → {value}")
                filled_count += 1
            else:
                output_lines.append(f"  ○ {label} [EMPTY]")
                empty_count += 1
        
        output_lines.append("")
        output_lines.append(f"  Summary: {filled_count} filled, {empty_count} empty")
        output_lines.append("")
    
    # Display key-value pairs
    if kv_pairs:
        output_lines.append("KEY-VALUE PAIRS")
        output_lines.append("-" * 80)
        for kv in kv_pairs:
            key = kv.get("Key", "")
            value = kv.get("Value", "")
            output_lines.append(f"  {key}: {value}")
        output_lines.append("")
    
    # Display checkboxes WITH STATE
    if checkboxes:
        output_lines.append("CHECKBOXES")
        output_lines.append("-" * 80)
        for cb in checkboxes:
            text = cb.get("Text", "")
            checked = cb.get("Checked", False)
            value = cb.get("Value", "")
            
            status = "☑ CHECKED" if checked else "☐ UNCHECKED"
            if value:
                output_lines.append(f"  {status}: {text} → {value}")
            else:
                output_lines.append(f"  {status}: {text}")
        output_lines.append("")
    
    # Display sections
    if sections:
        output_lines.append("SECTIONS")
        output_lines.append("-" * 80)
        for section in sections:
            output_lines.append(section["Title"])
            output_lines.append("-" * len(section["Title"]))
            output_lines.append("")
            
            if "Relationships" in section and section["Relationships"]:
                line_ids = section["Relationships"][0].get("Ids", [])
                for line_id in line_ids:
                    if line_id in line_dict:
                        output_lines.append(f"  {line_dict[line_id]['Text']}")
            
            output_lines.append("")
    
    # If no sections, print all lines
    if not sections and not form_fields:
        page_lines = [l for l in lines if l.get("Page") == page_number]
        page_lines.sort(key=lambda x: (
            x["Geometry"]["BoundingBox"]["Top"],
            x["Geometry"]["BoundingBox"]["Left"]
        ))
        
        for line in page_lines:
            output_lines.append(line["Text"])
    
    # Display tables WITH ACTUAL CELL CONTENT
    if tables:
        output_lines.append("")
        output_lines.append("TABLES")
        output_lines.append("-" * 80)
        
        for table_idx, table in enumerate(tables, 1):
            output_lines.append(f"\nTable {table_idx}:")
            output_lines.append("")
            
            cells = [b for b in blocks 
                    if b.get("BlockType") == "CELL" 
                    and b["Id"] in table["Relationships"][0]["Ids"]]
            
            # Organize cells into rows
            rows_dict = {}
            max_col = 0
            
            for cell in cells:
                row_idx = cell["RowIndex"]
                col_idx = cell["ColumnIndex"]
                max_col = max(max_col, col_idx)
                
                if row_idx not in rows_dict:
                    rows_dict[row_idx] = {}
                rows_dict[row_idx][col_idx] = cell["Text"]
            
            # Calculate column widths
            col_widths = {}
            for row_idx, row_cells in rows_dict.items():
                for col_idx in range(1, max_col + 1):
                    text = row_cells.get(col_idx, "")
                    col_widths[col_idx] = max(col_widths.get(col_idx, 10), len(text) + 2)
            
            # Print table with proper alignment
            for row_idx in sorted(rows_dict.keys()):
                row_parts = []
                for col_idx in range(1, max_col + 1):
                    text = rows_dict[row_idx].get(col_idx, "")
                    width = col_widths[col_idx]
                    row_parts.append(text.ljust(width))
                
                row_text = " | ".join(row_parts)
                output_lines.append(f"  {row_text}")
                
                # Add separator after header row
                if row_idx == 0:
                    separator = "-+-".join(["-" * col_widths[i] for i in range(1, max_col + 1)])
                    output_lines.append(f"  {separator}")
            
            output_lines.append("")
    
    return "\n".join(output_lines)


def create_structured_json(blocks, page_number):
    """Enhanced structured JSON with form fields"""
    result = {
        "page": page_number,
        "sections": [],
        "tables": [],
        "form_fields": [],
        "key_value_pairs": [],
        "checkboxes": []
    }
    
    # Extract sections
    sections = [b for b in blocks 
                if b.get("BlockType") == "SECTION" 
                and b.get("Page") == page_number]
    
    lines = [b for b in blocks if b.get("BlockType") == "LINE"]
    line_dict = {l["Id"]: l for l in lines}
    
    for section in sections:
        section_data = {
            "title": section["Title"],
            "content": []
        }
        
        if "Relationships" in section and section["Relationships"]:
            line_ids = section["Relationships"][0].get("Ids", [])
            for line_id in line_ids:
                if line_id in line_dict:
                    line = line_dict[line_id]
                    section_data["content"].append({
                        "text": line["Text"],
                        "confidence": line.get("Confidence", 0),
                        "bbox": line["Geometry"]["BoundingBox"]
                    })
        
        result["sections"].append(section_data)
    
    # Extract form fields WITH VALUES
    form_fields = [b for b in blocks 
                   if b.get("BlockType") == "FORM_FIELD" 
                   and b.get("Page") == page_number]
    
    for field in form_fields:
        result["form_fields"].append({
            "label": field.get("Label", ""),
            "value": field.get("Value", ""),
            "has_value": field.get("HasValue", False),
            "bbox": field["Geometry"]["BoundingBox"]
        })
    
    # Extract key-value pairs
    kv_pairs = [b for b in blocks 
                if b.get("BlockType") == "KEY_VALUE_SET" 
                and b.get("Page") == page_number]
    
    for kv in kv_pairs:
        result["key_value_pairs"].append({
            "key": kv.get("Key", ""),
            "value": kv.get("Value", ""),
            "bbox": kv["Geometry"]["BoundingBox"]
        })
    
    # Extract checkboxes WITH STATE
    checkboxes = [b for b in blocks 
                  if b.get("BlockType") == "CHECKBOX" 
                  and b.get("Page") == page_number]
    
    for cb in checkboxes:
        result["checkboxes"].append({
            "text": cb.get("Text", ""),
            "checked": cb.get("Checked", False),
            "value": cb.get("Value", ""),
            "bbox": cb["Geometry"]["BoundingBox"]
        })
    
    # Extract tables
    tables = [b for b in blocks 
              if b.get("BlockType") == "TABLE" 
              and b.get("Page") == page_number]
    
    for table in tables:
        cells = [b for b in blocks 
                if b.get("BlockType") == "CELL" 
                and b["Id"] in table["Relationships"][0]["Ids"]]
        
        table_data = {"rows": [], "has_header": True}
        rows_dict = {}
        
        for cell in cells:
            row_idx = cell["RowIndex"]
            if row_idx not in rows_dict:
                rows_dict[row_idx] = []
            rows_dict[row_idx].append({
                "text": cell["Text"],
                "column": cell["ColumnIndex"],
                "confidence": cell.get("Confidence", 0),
                "is_header": cell.get("IsHeader", False)
            })
        
        for row_idx in sorted(rows_dict.keys()):
            row_cells = sorted(rows_dict[row_idx], key=lambda x: x["column"])
            table_data["rows"].append([c["text"] for c in row_cells])
        
        result["tables"].append(table_data)
    
    return result


def save_readable_output(blocks, output_path):
    """Save enhanced outputs"""
    pages = set()
    for block in blocks:
        if "Page" in block:
            pages.add(block["Page"])
    
    if not pages:
        print("Warning: No pages found in blocks!")
        return
    
    # Save text output
    text_output = []
    for page_num in sorted(pages):
        text_output.append(format_readable_output(blocks, page_num))
        text_output.append("\n\n")
    
    text_path = output_path.replace('.json', '_readable.txt')
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(text_output))
    print(f"✅ Saved readable text to: {text_path}")
    
    # Save structured JSON
    json_output = {"pages": []}
    for page_num in sorted(pages):
        json_output["pages"].append(create_structured_json(blocks, page_num))
    
    json_path = output_path.replace('.json', '_structured.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved structured JSON to: {json_path}")