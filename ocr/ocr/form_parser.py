import re
from ocr.block_factory import create_block


def is_form_field_label(text):
    text = text.strip()

    if len(text) < 2:
        return False

    if re.match(r"^\d+[A-Z]\.\s", text):
        return True

    if text.endswith(":") and len(text) < 50 and len(text.split()) <= 5:
        return True

    if re.search(r"\bYes\s+No\b", text, re.IGNORECASE) and len(text) < 30:
        return True

    return False


def extract_value_from_nearby_words(line, all_words, search_radius=0.05):
    label_bbox = line["Geometry"]["BoundingBox"]
    label_right = label_bbox["Left"] + label_bbox["Width"]
    label_bottom = label_bbox["Top"] + label_bbox["Height"]
    label_top = label_bbox["Top"]
    label_text = line["Text"].strip()

    same_line_words = []
    for word in all_words:
        word_bbox = word["Geometry"]["BoundingBox"]
        word_left = word_bbox["Left"]
        word_top = word_bbox["Top"]
        word_text = word["Text"].strip()

        if word_text in label_text:
            continue

        if is_form_field_label(word_text):
            continue

        skip_words = ["to:", "go", "or", "mail", "form", "paper", "online"]
        if word_text.lower() in skip_words:
            continue

        if (
            word_left > label_right
            and word_left < label_right + 0.3
            and abs(word_top - label_top) < 0.015
        ):
            same_line_words.append(word)

    same_line_words.sort(key=lambda w: w["Geometry"]["BoundingBox"]["Left"])

    if same_line_words:
        value_words = [same_line_words[0]]
        prev_right = (
            same_line_words[0]["Geometry"]["BoundingBox"]["Left"]
            + same_line_words[0]["Geometry"]["BoundingBox"]["Width"]
        )

        for word in same_line_words[1:]:
            word_left = word["Geometry"]["BoundingBox"]["Left"]
            gap = word_left - prev_right
            if gap > 0.05:
                break
            value_words.append(word)
            prev_right = word_left + word["Geometry"]["BoundingBox"]["Width"]

        result = " ".join(w["Text"] for w in value_words[:5])

        if not is_form_field_label(result) and len(result) > 0:
            return result

    below_words = []
    for word in all_words:
        word_bbox = word["Geometry"]["BoundingBox"]
        word_top = word_bbox["Top"]
        word_left = word_bbox["Left"]
        word_text = word["Text"].strip()

        if word_text in label_text:
            continue

        if is_form_field_label(word_text):
            continue

        if (
            word_top > label_bottom
            and word_top < label_bottom + 0.025
            and abs(word_left - label_bbox["Left"]) < 0.05
        ):
            below_words.append(word)

    below_words.sort(
        key=lambda w: (
            w["Geometry"]["BoundingBox"]["Top"],
            w["Geometry"]["BoundingBox"]["Left"],
        )
    )

    if below_words:
        result = " ".join(w["Text"] for w in below_words[:6])
        if not is_form_field_label(result) and len(result) > 0:
            return result

    return ""


def split_multi_field_line(text):
    pattern = r"(\d+[A-Z]\.\s+[^:]+:?)"
    matches = re.findall(pattern, text)

    if len(matches) > 1:
        fields = []
        for match in matches:
            field = match.strip()
            if not field.endswith(":"):
                field += ":"
            fields.append(field)
        return fields

    return [text]


def extract_form_fields_with_values(line_blocks, word_blocks):
    form_fields = []

    page_words = {}
    for word in word_blocks:
        page = word.get("Page", 1)
        if page not in page_words:
            page_words[page] = []
        page_words[page].append(word)

    for line in line_blocks:
        text = line["Text"].strip()

        if len(text) > 100:
            continue

        skip_phrases = [
            "online submission",
            "paper form",
            "mail to",
            "go to",
            "important:",
            "note:",
            "instructions",
            "form submission",
            "complete all",
            "attach copies",
            "please verify",
            "medical services",
            "took place",
            "indiana law",
            "requires us",
            "questions or guidance",
        ]
        text_lower = text.lower()
        if any(phrase in text_lower for phrase in skip_phrases):
            continue

        instruction_verbs = [
            "complete",
            "attach",
            "provide",
            "submit",
            "verify",
            "indicate",
            "send",
            "must",
            "should",
            "requires",
        ]
        if any(verb in text_lower for verb in instruction_verbs):
            continue

        field_count = len(re.findall(r"\d+[A-Z]\.", text))

        if field_count > 1:
            individual_fields = split_multi_field_line(text)
            for field_text in individual_fields:
                if is_form_field_label(field_text):
                    field_block = create_block(
                        "FORM_FIELD",
                        Label=field_text,
                        Value="",
                        HasValue=False,
                        Page=line.get("Page", 1),
                        Geometry=line["Geometry"],
                        Relationships=[{"Type": "CHILD", "Ids": [line["Id"]]}],
                    )
                    form_fields.append(field_block)
            continue

        if not is_form_field_label(text):
            continue

        page = line.get("Page", 1)
        words_on_page = page_words.get(page, [])

        label = text
        value_text = ""

        prefix_match = re.match(r"^(\d+[A-Z]\.)\s+(.*)$", text)
        if prefix_match:
            prefix = prefix_match.group(1) + " "
            rest = prefix_match.group(2).strip()

            if rest.endswith(":"):
                rest_no_colon = rest[:-1].strip()
                words = rest_no_colon.split()

                field_keywords = {
                    "name", "gender", "date", "birth", "address", "mailing",
                    "city", "state", "postal", "code", "country",
                    "telephone", "email", "policy", "certificate",
                    "citizenship", "home", "visited"
                }

                label_starters = [
                    "claimant", "gender", "date", "current", "primary",
                    "secondary", "email", "policy", "citizenship", "home",
                    "countries", "state", "city", "postal", "country"
                ]

                best_split = None
                best_score = -1

                for i in range(1, len(words)):
                    left_part = " ".join(words[:i]).strip()
                    right_part = " ".join(words[i:]).strip()
                    right_lower = right_part.lower()

                    if not any(k in right_lower for k in field_keywords):
                        continue

                    if len(right_part.split()) > 12:
                        continue

                    # value must look like something fillable
                    looks_like_value = False
                    if re.match(r"^\d{2}/\d{2}/\d{4}$", left_part):
                        looks_like_value = True
                    elif left_part.lower() in ["male", "female", "m", "f"]:
                        looks_like_value = True
                    elif re.match(r"^\S+@\S+\.\S+$", left_part):
                        looks_like_value = True
                    elif re.match(r"^\d{6,}$", left_part):
                        looks_like_value = True
                    elif re.match(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+){0,3}$", left_part):
                        looks_like_value = True

                    if not looks_like_value:
                        continue

                    # scoring: prefer more complete values (2 words for names)
                    score = 0
                    score += min(len(left_part.split()), 4) * 5

                    # prefer labels that start like real field names
                    if any(right_lower.startswith(st) for st in label_starters):
                        score += 20

                    # prefer labels containing strong form terms
                    if "full name" in right_lower:
                        score += 15
                    if "date of birth" in right_lower:
                        score += 15
                    if "mailing address" in right_lower:
                        score += 10

                    # penalize labels that still contain obvious person-name fragments
                    if re.search(r"\b[A-Z][a-z]+\b", right_part) and "name" in right_lower:
                        score -= 5

                    if score > best_score:
                        best_score = score
                        best_split = (left_part, right_part)

                if best_split:
                    embedded_val, embedded_label = best_split
                    label = prefix + embedded_label + ":"
                    value_text = embedded_val

        if not value_text:
            value_text = extract_value_from_nearby_words(line, words_on_page)

        if value_text:
            if "http" in value_text.lower() or "www." in value_text.lower():
                value_text = ""

            if is_form_field_label(value_text):
                value_text = ""

            if re.match(r"^[\W_]+$", value_text):
                value_text = ""

            if len(re.findall(r"\d+[A-Z]\.", value_text)) > 0:
                value_text = ""

        embedded_value = ""
        if ":" in label and not label.endswith(":"):
            parts = label.split(":", 1)
            if len(parts) == 2 and parts[1].strip():
                embedded_value = parts[1].strip()
                label = parts[0] + ":"

        final_value = embedded_value if embedded_value else value_text

        field_block = create_block(
            "FORM_FIELD",
            Label=label,
            Value=final_value,
            HasValue=bool(final_value),
            Page=page,
            Geometry=line["Geometry"],
            Relationships=[{"Type": "CHILD", "Ids": [line["Id"]]}],
        )
        form_fields.append(field_block)

    return form_fields



def detect_checkboxes_with_state(word_blocks, line_blocks):
    checkboxes = []

    checkbox_patterns = [
        (r"☐", False),
        (r"☑", True),
        (r"☒", True),
        (r"□", False),
        (r"■", True),
        (r"\[\s*\]", False),
        (r"\[X\]", True),
        (r"\[x\]", True),
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
                    Geometry=word["Geometry"],
                )
                checkboxes.append(checkbox_block)
                break

    for line in line_blocks:
        text = line["Text"].strip()

        if re.search(r"\bYes\s+No\b", text, re.IGNORECASE):
            yes_checked = bool(re.search(r"Yes\s*[X☑☒■]", text, re.IGNORECASE))
            no_checked = bool(re.search(r"No\s*[X☑☒■]", text, re.IGNORECASE))

            if yes_checked or no_checked:
                checkbox_block = create_block(
                    "CHECKBOX",
                    Text=text,
                    Checked=yes_checked,
                    Value="Yes" if yes_checked else "No",
                    Page=line.get("Page", 1),
                    Geometry=line["Geometry"],
                )
                checkboxes.append(checkbox_block)

    return checkboxes


def extract_key_value_pairs(line_blocks):
    kv_pairs = []

    for line in line_blocks:
        text = line["Text"].strip()

        if ":" in text:
            parts = text.split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()

                # ✅ FIXED: prevent paragraphs + multi-field lines being treated as KV
                if (
                    value
                    and len(key.split()) <= 6
                    and len(text) < 120
                    and len(re.findall(r"\d+[A-Z]\.", text)) <= 1
                ):
                    kv_block = create_block(
                        "KEY_VALUE_SET",
                        Key=key,
                        Value=value,
                        Page=line.get("Page", 1),
                        Geometry=line["Geometry"],
                        Relationships=[{"Type": "CHILD", "Ids": [line["Id"]]}],
                    )
                    kv_pairs.append(kv_block)

    return kv_pairs


def detect_multi_column_layout(line_blocks, column_threshold=0.4):
    if not line_blocks:
        return []

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
            Relationships=[{"Type": "CHILD", "Ids": [l["Id"] for l in left_column]}],
        )
        columns.append(col_block)

    if right_column:
        col_block = create_block(
            "COLUMN",
            ColumnIndex=2,
            LineCount=len(right_column),
            Page=right_column[0].get("Page", 1),
            Relationships=[{"Type": "CHILD", "Ids": [l["Id"] for l in right_column]}],
        )
        columns.append(col_block)

    return columns


def build_form_blocks(line_blocks, word_blocks):
    all_form_blocks = []

    form_fields = extract_form_fields_with_values(line_blocks, word_blocks)
    all_form_blocks.extend(form_fields)

    checkboxes = detect_checkboxes_with_state(word_blocks, line_blocks)
    all_form_blocks.extend(checkboxes)

    kv_pairs = extract_key_value_pairs(line_blocks)
    all_form_blocks.extend(kv_pairs)

    columns = detect_multi_column_layout(line_blocks)
    all_form_blocks.extend(columns)

    return all_form_blocks
