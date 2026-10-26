
import fitz
import pytest

from backend.pdf_processor import extract_text_from_pdf


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF containing text on two pages."""
    pdf_path = tmp_path / "sample.pdf"

    with fitz.open() as pdf:
        page1 = pdf.new_page()
        page1.insert_text((72, 72), "DocuMind AI extracts PDF text.")

        page2 = pdf.new_page()
        page2.insert_text((72, 72), "This is the second page.")

        pdf.save(pdf_path)

    return str(pdf_path)


def test_extract_text_from_valid_pdf(sample_pdf):
    """Verify that text is extracted from a valid PDF."""
    result = extract_text_from_pdf(sample_pdf)

    assert "DocuMind AI extracts PDF text." in result
    assert "This is the second page." in result


def test_page_numbers_are_included(sample_pdf):
    """Verify that extracted text includes page markers."""
    result = extract_text_from_pdf(sample_pdf)

    assert "--- Page 1 ---" in result
    assert "--- Page 2 ---" in result


def test_pages_are_extracted_in_order(sample_pdf):
    """Verify that the first page appears before the second."""
    result = extract_text_from_pdf(sample_pdf)

    first_page_position = result.index("DocuMind AI extracts PDF text.")
    second_page_position = result.index("This is the second page.")

    assert first_page_position < second_page_position



def test_pdf_without_text_returns_empty_string(tmp_path):
    """Verify that a PDF containing a blank page produces an empty string."""
    pdf_path = tmp_path / "blank.pdf"

    with fitz.open() as pdf:
        pdf.new_page()
        pdf.save(pdf_path)

    result = extract_text_from_pdf(str(pdf_path))

    assert result == ""



def test_invalid_pdf_raises_error(tmp_path):
    """Verify that an invalid PDF raises an exception."""
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_text("This is not a valid PDF.", encoding="utf-8")

    with pytest.raises(Exception):
        extract_text_from_pdf(str(pdf_path))


def test_missing_pdf_raises_error(tmp_path):
    """Verify that a nonexistent PDF raises an exception."""
    pdf_path = tmp_path / "missing.pdf"

    with pytest.raises(Exception):
        extract_text_from_pdf(str(pdf_path))
