import os

BASE_DIR = "ocr"

structure = [
    "data",
    "output",
    "ocr"
]

files = {
    "data/sample.pdf": "",
    "output/result.json": "",
    "ocr/__init__.py": "",
    "ocr/pdf_loader.py": "",
    "ocr/image_preprocessor.py": "",
    "ocr/tesseract_engine.py": "",
    "ocr/json_formatter.py": "",
    "config.py": "",
    "main.py": "",
    "requirements.txt": "",
    "README.md": ""
}

# Create base directory
os.makedirs(BASE_DIR, exist_ok=True)

# Create folders
for folder in structure:
    os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)

# Create files
for path, content in files.items():
    full_path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ OCR project structure created successfully!")
