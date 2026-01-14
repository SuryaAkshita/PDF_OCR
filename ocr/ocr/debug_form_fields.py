"""
Debug visualizer to see what's being detected as form fields and their values
"""
import json


def visualize_form_field_detection(blocks, page_number):
    """
    Create a detailed debug output showing exactly what was detected
    """
    print("\n" + "="*80)
    print(f"DEBUG: Form Field Detection for Page {page_number}")
    print("="*80)
    
    # Get form fields
    form_fields = [b for b in blocks 
                   if b.get("BlockType") == "FORM_FIELD" 
                   and b.get("Page") == page_number]
    
    # Get all lines for reference
    lines = [b for b in blocks 
             if b.get("BlockType") == "LINE" 
             and b.get("Page") == page_number]
    
    print(f"\nTotal form fields detected: {len(form_fields)}")
    print(f"Total lines on page: {len(lines)}")
    print("\n" + "-"*80)
    
    for i, field in enumerate(form_fields, 1):
        label = field.get("Label", "")
        value = field.get("Value", "")
        has_value = field.get("HasValue", False)
        
        print(f"\n[Field {i}]")
        print(f"  Label: '{label}'")
        print(f"  Value: '{value}'")
        print(f"  Has Value: {has_value}")
        print(f"  Status: {'✓ FILLED' if has_value else '○ EMPTY'}")
        
        # Show geometry for debugging
        bbox = field["Geometry"]["BoundingBox"]
        print(f"  Position: Top={bbox['Top']:.3f}, Left={bbox['Left']:.3f}")
    
    print("\n" + "="*80)
    
    # Show some sample lines for context
    print("\nSample Lines (first 10):")
    print("-"*80)
    for i, line in enumerate(lines[:10], 1):
        print(f"{i}. {line['Text']}")
    
    print("\n")


def debug_ocr_output(output_json_path):
    """
    Load and debug OCR output
    """
    with open(output_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    blocks = data.get("Blocks", [])
    
    # Get unique pages
    pages = set()
    for block in blocks:
        if "Page" in block:
            pages.add(block["Page"])
    
    # Visualize each page
    for page_num in sorted(pages):
        visualize_form_field_detection(blocks, page_num)


if __name__ == "__main__":
    # Debug the output
    debug_ocr_output("output/output_blocks.json")