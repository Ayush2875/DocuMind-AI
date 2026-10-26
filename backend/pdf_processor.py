import fitz


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from every page of a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text as a single string.
    """
    extracted_text = []

    with fitz.open(file_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            page_text = page.get_text()

            if page_text.strip():
                extracted_text.append(
                    f"\n--- Page {page_number} ---\n{page_text}"
                )

    return "\n".join(extracted_text).strip()