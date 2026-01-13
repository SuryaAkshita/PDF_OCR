import fitz  # PyMuPDF
import numpy as np

def pdf_to_images(pdf_path, dpi=300):
    doc = fitz.open(pdf_path)
    pages = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        pix = page.get_pixmap(dpi=dpi)

        img = np.frombuffer(pix.samples, dtype=np.uint8)
        img = img.reshape(pix.height, pix.width, pix.n)

        pages.append({
            "page_number": page_index + 1,
            "image": img
        })

    return pages