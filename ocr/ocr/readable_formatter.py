import json


def format_readable_output(blocks, page_number):
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append(f"PAGE {page_number}")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    # FIX: Filter sections by page
    sections = [b for b in blocks 
                if b.get("BlockType") == "SECTION" 
                and b.get("Page") == page_number]
    
    # Get ALL lines (we'll filter by ID later)
    lines = [b for b in blocks if b.get("BlockType") == "LINE"]
    line_dict = {l["Id"]: l for l in lines}
    
    # FIX: Filter tables by page
    tables = [b for b in blocks 
              if b.get("BlockType") == "TABLE" 
              and b.get("Page") == page_number]
    
    if sections:
        for section in sections:
            # Section title
            output_lines.append(section["Title"])
            output_lines.append("-" * len(section["Title"]))
            output_lines.append("")
            
            # Section content (lines)
            if "Relationships" in section and section["Relationships"]:
                line_ids = section["Relationships"][0].get("Ids", [])
                for line_id in line_ids:
                    if line_id in line_dict:
                        output_lines.append(f"  {line_dict[line_id]['Text']}")
            
            output_lines.append("")
    
    # If no sections, just print all lines for this page
    else:
        page_lines = [l for l in lines if l.get("Page") == page_number]
        page_lines.sort(key=lambda x: (
            x["Geometry"]["BoundingBox"]["Top"],
            x["Geometry"]["BoundingBox"]["Left"]
        ))
        
        for line in page_lines:
            output_lines.append(line["Text"])
    
    # Add tables for this page
    if tables:
        output_lines.append("")
        output_lines.append("TABLES")
        output_lines.append("-" * 80)
        
        for table in tables:
            output_lines.append("")
            cells = [b for b in blocks 
                    if b.get("BlockType") == "CELL" 
                    and b["Id"] in table["Relationships"][0]["Ids"]]
            
            # Organize cells into rows
            rows_dict = {}
            for cell in cells:
                row_idx = cell["RowIndex"]
                if row_idx not in rows_dict:
                    rows_dict[row_idx] = []
                rows_dict[row_idx].append(cell)
            
            # Print table
            for row_idx in sorted(rows_dict.keys()):
                row_cells = sorted(rows_dict[row_idx], key=lambda x: x["ColumnIndex"])
                row_text = " | ".join(c["Text"] for c in row_cells)
                output_lines.append(f"  {row_text}")
    
    return "\n".join(output_lines)


def create_structured_json(blocks, page_number):
    result = {
        "page": page_number,
        "sections": [],
        "tables": []
    }
    
    # FIX: Filter sections by page
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
    
    # FIX: Filter tables by page
    tables = [b for b in blocks 
              if b.get("BlockType") == "TABLE" 
              and b.get("Page") == page_number]
    
    for table in tables:
        cells = [b for b in blocks 
                if b.get("BlockType") == "CELL" 
                and b["Id"] in table["Relationships"][0]["Ids"]]
        
        # Organize cells into rows
        table_data = {"rows": []}
        rows_dict = {}
        
        for cell in cells:
            row_idx = cell["RowIndex"]
            if row_idx not in rows_dict:
                rows_dict[row_idx] = []
            rows_dict[row_idx].append({
                "text": cell["Text"],
                "column": cell["ColumnIndex"],
                "confidence": cell.get("Confidence", 0)
            })
        
        for row_idx in sorted(rows_dict.keys()):
            row_cells = sorted(rows_dict[row_idx], key=lambda x: x["column"])
            table_data["rows"].append([c["text"] for c in row_cells])
        
        result["tables"].append(table_data)
    
    return result


def save_readable_output(blocks, output_path):
    """
    Save both text and JSON readable outputs
    
    Args:
        blocks: List of all blocks
        output_path: Base path for output files
    """
    # Determine number of pages
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
    print(f"Saved readable text to: {text_path}")
    
    # Save structured JSON
    json_output = {"pages": []}
    for page_num in sorted(pages):
        json_output["pages"].append(create_structured_json(blocks, page_num))
    
    json_path = output_path.replace('.json', '_structured.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    print(f"Saved structured JSON to: {json_path}")