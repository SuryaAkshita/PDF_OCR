"""
Enhanced form parser for detecting form fields with VALUES, checkboxes, and key-value pairs
"""
import re
from ocr.block_factory import create_block


def is_form_field_label(text):
    """
    Detect if text is likely a form field label
    Examples: "Name:", "1A.", "Date of Birth:", "Yes No"
    """
    text = text.strip()
    
    # Empty or very short text is not a label
    if len(text) < 2:
        return False
    
    # Pattern 1: Numbered field (e.g., "1A.", "12B.", "3C.")
    # This is the MOST RELIABLE pattern for forms
    if re.match(r'^\d+[A-Z]\.\s', text):
        return True
    
    # Pattern 2: Single field ending with colon, short text
    # BUT exclude long instructional text
    if text.endswith(':') and len(text) < 50 and len(text.split()) <= 5:
        return True
    
    # Pattern 3: Yes/No checkbox pairs (but must be short)
    if re.search(r'\bYes\s+No\b', text, re.IGNORECASE) and len(text) < 30:
        return True
    
    # Everything else is NOT a form field label
    return False


def extract_value_from_nearby_words(line, all_words, search_radius=0.05):
    """
    Extract values by looking at words to the right of or below the label
    
    Args:
        line: The label line block
        all_words: All word blocks on the page
        search_radius: How far to search (in normalized coordinates)
    
    Returns:
        Extracted value text
    """
    label_bbox = line["Geometry"]["BoundingBox"]
    label_right = label_bbox["Left"] + label_bbox["Width"]
    label_bottom = label_bbox["Top"] + label_bbox["Height"]
    label_top = label_bbox["Top"]
    label_text = line["Text"].strip()
    
    # Look for words to the right (same line)
    same_line_words = []
    for word in all_words:
        word_bbox = word["Geometry"]["BoundingBox"]
        word_left = word_bbox["Left"]
        word_top = word_bbox["Top"]
        word_text = word["Text"].strip()
        
        # Skip if this word is part of the label itself
        if word_text in label_text:
            continue
        
        # Skip if it's another form field label
        if is_form_field_label(word_text):
            continue
        
        # Skip common label keywords that aren't values
        skip_words = ['to:', 'go', 'or', 'mail', 'form', 'paper', 'online']
        if word_text.lower() in skip_words:
            continue
        
        # Word is to the right and on roughly the same line
        if (word_left > label_right and 
            word_left < label_right + 0.3 and  # Not too far right
            abs(word_top - label_top) < 0.015):  # Same vertical position (tighter tolerance)
            same_line_words.append(word)
    
    # Sort by horizontal position
    same_line_words.sort(key=lambda w: w["Geometry"]["BoundingBox"]["Left"])
    
    if same_line_words:
        # Only take words that are reasonably close together
        value_words = [same_line_words[0]]
        prev_right = same_line_words[0]["Geometry"]["BoundingBox"]["Left"] + \
                     same_line_words[0]["Geometry"]["BoundingBox"]["Width"]
        
        for word in same_line_words[1:]:
            word_left = word["Geometry"]["BoundingBox"]["Left"]
            gap = word_left - prev_right
            
            # If gap is too large (> 0.05), stop collecting words
            if gap > 0.05:
                break
            
            value_words.append(word)
            prev_right = word_left + word["Geometry"]["BoundingBox"]["Width"]
        
        # Return value if we have reasonable content
        result = " ".join(w["Text"] for w in value_words[:5])  # Max 5 words
        
        # Validate: must not be another form label
        if not is_form_field_label(result) and len(result) > 0:
            return result
    
    # Look for words below (next line) - but be very strict
    below_words = []
    for word in all_words:
        word_bbox = word["Geometry"]["BoundingBox"]
        word_top = word_bbox["Top"]
        word_left = word_bbox["Left"]
        word_text = word["Text"].strip()
        
        # Skip if part of label
        if word_text in label_text:
            continue
        
        # Skip if it's another form field label
        if is_form_field_label(word_text):
            continue
        
        # Word is directly below (similar horizontal alignment)
        if (word_top > label_bottom and 
            word_top < label_bottom + 0.025 and  # Very close vertically
            abs(word_left - label_bbox["Left"]) < 0.05):  # Similar left alignment
            below_words.append(word)
    
    # Sort by position
    below_words.sort(key=lambda w: (
        w["Geometry"]["BoundingBox"]["Top"],
        w["Geometry"]["BoundingBox"]["Left"]
    ))
    
    if below_words:
        result = " ".join(w["Text"] for w in below_words[:6])  # Max 6 words
        
        # Validate: must not be another form label
        if not is_form_field_label(result) and len(result) > 0:
            return result
    
    return ""


def split_multi_field_line(text):
    """
    Split lines that contain multiple form fields
    Example: "1A. Name: 2A. Gender: 3A. DOB:" -> ["1A. Name:", "2A. Gender:", "3A. DOB:"]
    """
    # Find all field patterns
    pattern = r'(\d+[A-Z]\.\s+[^:]+:?)'
    matches = re.findall(pattern, text)
    
    if len(matches) > 1:
        # Multiple fields found
        fields = []
        for match in matches:
            field = match.strip()
            if not field.endswith(':'):
                field += ':'
            fields.append(field)
        return fields
    
    return [text]  # Single field or no match


def extract_form_fields_with_values(line_blocks, word_blocks):
    """
    Extract form fields WITH their filled values
    Returns list of form field blocks with values
    """
    form_fields = []
    
    # Create a lookup for quick word access by page
    page_words = {}
    for word in word_blocks:
        page = word.get("Page", 1)
        if page not in page_words:
            page_words[page] = []
        page_words[page].append(word)
    
    for line in line_blocks:
        text = line["Text"].strip()
        
        # CRITICAL: Skip long instructional text
        if len(text) > 100:  # Long text is never a form field
            continue
        
        # Skip navigation/instruction text
        skip_phrases = [
            'online submission', 'paper form', 'mail to', 'go to',
            'important:', 'note:', 'instructions', 'form submission',
            'complete all', 'attach copies', 'please verify',
            'medical services', 'took place', 'indiana law', 'requires us'
        ]
        text_lower = text.lower()
        if any(phrase in text_lower for phrase in skip_phrases):
            continue
        
        # Skip lines that are clearly instructions (contain verbs)
        instruction_verbs = ['complete', 'attach', 'provide', 'submit', 'verify', 'indicate', 'send', 'must', 'should', 'requires']
        if any(verb in text_lower for verb in instruction_verbs):
            continue
        
        # Check if line contains multiple form fields
        field_count = len(re.findall(r'\d+[A-Z]\.', text))
        
        if field_count > 1:
            # Split into individual fields
            individual_fields = split_multi_field_line(text)
            
            for field_text in individual_fields:
                if is_form_field_label(field_text):
                    field_block = create_block(
                        "FORM_FIELD",
                        Label=field_text,
                        Value="",  # Multi-field lines don't have values inline
                        HasValue=False,
                        Page=line.get("Page", 1),
                        Geometry=line["Geometry"],
                        Relationships=[{
                            "Type": "CHILD",
                            "Ids": [line["Id"]]
                        }]
                    )
                    form_fields.append(field_block)
            continue  # Move to next line
        
        # Single field processing
        if not is_form_field_label(text):
            continue
        
        page = line.get("Page", 1)
        words_on_page = page_words.get(page, [])
        
        # Extract value from nearby words
        value_text = extract_value_from_nearby_words(line, words_on_page)
        
        # Additional validation: check if value is likely valid
        if value_text:
            # Skip if value looks like a URL
            if 'http' in value_text.lower() or 'www.' in value_text.lower():
                value_text = ""
            
            # Skip if value looks like another form label
            if is_form_field_label(value_text):
                value_text = ""
            
            # Skip if value is just punctuation or special chars
            if re.match(r'^[\W_]+$', value_text):
                value_text = ""
            
            # Skip if value contains multiple field numbers
            if len(re.findall(r'\d+[A-Z]\.', value_text)) > 0:
                value_text = ""
        
        # Also check if value is embedded in the same line
        # e.g., "Name: John Doe" -> label="Name:", value="John Doe"
        embedded_value = ""
        if ':' in text and not text.endswith(':'):
            parts = text.split(':', 1)
            if len(parts) == 2 and parts[1].strip():
                embedded_value = parts[1].strip()
                text = parts[0] + ':'  # Keep just the label
        
        # Prefer embedded value over nearby value
        final_value = embedded_value if embedded_value else value_text
        
        field_block = create_block(
            "FORM_FIELD",
            Label=text,
            Value=final_value,
            HasValue=bool(final_value),
            Page=page,
            Geometry=line["Geometry"],
            Relationships=[{
                "Type": "CHILD",
                "Ids": [line["Id"]]
            }]
        )
        form_fields.append(field_block)
    
    return form_fields


def detect_checkboxes_with_state(word_blocks, line_blocks):
    """
    Detect checkboxes and determine if they're checked
    Returns list of checkbox blocks with state
    """
    checkboxes = []
    
    # Pattern 1: Look for checkbox indicators in words
    checkbox_patterns = [
        (r'☐', False), (r'☑', True), (r'☒', True), (r'□', False), (r'■', True),
        (r'\[\s*\]', False), (r'\[X\]', True), (r'\[x\]', True),
    ]
    
    for word in word_blocks:
        text = word["Text"].strip()
        
        for pattern, is_checked in checkbox_patterns:
            if re.search(pattern, text):
                checkbox_block = create_block(
                    "CHECKBOX",
                    Text=text,
                    Checked=is_checked,
                    Page=word.get("Page", 1),
                    Geometry=word["Geometry"]
                )
                checkboxes.append(checkbox_block)
                break
    
    # Pattern 2: Yes/No pairs in lines
    for line in line_blocks:
        text = line["Text"].strip()
        
        # Look for "Yes No" patterns
        if re.search(r'\bYes\s+No\b', text, re.IGNORECASE):
            # Try to determine which is checked
            # Look for patterns like "Yes ☑ No ☐" or "Yes X No"
            yes_checked = bool(re.search(r'Yes\s*[X☑☒■]', text, re.IGNORECASE))
            no_checked = bool(re.search(r'No\s*[X☑☒■]', text, re.IGNORECASE))
            
            if yes_checked or no_checked:
                checkbox_block = create_block(
                    "CHECKBOX",
                    Text=text,
                    Checked=yes_checked,
                    Value="Yes" if yes_checked else "No",
                    Page=line.get("Page", 1),
                    Geometry=line["Geometry"]
                )
                checkboxes.append(checkbox_block)
    
    return checkboxes


def extract_key_value_pairs(line_blocks):
    """
    Extract key-value pairs from lines
    Example: "Name: John Doe" -> {"Name": "John Doe"}
    """
    kv_pairs = []
    
    for line in line_blocks:
        text = line["Text"].strip()
        
        # Pattern 1: "Label: Value"
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                
                # Only create KV pair if:
                # 1. Value exists and is not empty
                # 2. Key is reasonable length (not a paragraph)
                if value and len(key.split()) <= 6:
                    kv_block = create_block(
                        "KEY_VALUE_SET",
                        Key=key,
                        Value=value,
                        Page=line.get("Page", 1),
                        Geometry=line["Geometry"],
                        Relationships=[{
                            "Type": "CHILD",
                            "Ids": [line["Id"]]
                        }]
                    )
                    kv_pairs.append(kv_block)
    
    return kv_pairs


def detect_multi_column_layout(line_blocks, column_threshold=0.4):
    """
    Detect if page has multi-column layout
    Returns list of column groups
    """
    if not line_blocks:
        return []
    
    # Group lines by their X position
    left_column = []
    right_column = []
    
    for line in line_blocks:
        left = line["Geometry"]["BoundingBox"]["Left"]
        
        if left < column_threshold:
            left_column.append(line)
        else:
            right_column.append(line)
    
    columns = []
    
    if left_column:
        col_block = create_block(
            "COLUMN",
            ColumnIndex=1,
            LineCount=len(left_column),
            Page=left_column[0].get("Page", 1),
            Relationships=[{
                "Type": "CHILD",
                "Ids": [l["Id"] for l in left_column]
            }]
        )
        columns.append(col_block)
    
    if right_column:
        col_block = create_block(
            "COLUMN",
            ColumnIndex=2,
            LineCount=len(right_column),
            Page=right_column[0].get("Page", 1),
            Relationships=[{
                "Type": "CHILD",
                "Ids": [l["Id"] for l in right_column]
            }]
        )
        columns.append(col_block)
    
    return columns


def build_form_blocks(line_blocks, word_blocks):
    """
    Main function to extract all form-related blocks WITH VALUES
    """
    all_form_blocks = []
    
    # Extract form fields WITH values
    form_fields = extract_form_fields_with_values(line_blocks, word_blocks)
    all_form_blocks.extend(form_fields)
    
    # Detect checkboxes WITH state
    checkboxes = detect_checkboxes_with_state(word_blocks, line_blocks)
    all_form_blocks.extend(checkboxes)
    
    # Extract key-value pairs
    kv_pairs = extract_key_value_pairs(line_blocks)
    all_form_blocks.extend(kv_pairs)
    
    # Detect columns
    columns = detect_multi_column_layout(line_blocks)
    all_form_blocks.extend(columns)
    
    return all_form_blocks