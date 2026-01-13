def format_document_output(file_name, pages_data):
    return {
        "document_metadata": {
            "file_name": file_name,
            "total_pages": len(pages_data)
        },
        "pages": pages_data
    }
