from pathlib import Path

from app.services.extractors import clean_text, read_docx, read_pdf

SAMPLES = Path(__file__).parent.parent / "samples"


def test_read_pdf_gives_one_text_per_page():
    pages = read_pdf((SAMPLES / "policy.pdf").read_bytes())

    assert len(pages) == 3
    assert "Employee Leave and Remote Work Policy" in pages[0]
    assert "Effective 1 April 2026" in pages[0]  # "ff" is a ligature in this PDF


def test_read_docx_with_table():
    text = read_docx((SAMPLES / "handbook.docx").read_bytes())

    assert "IT Onboarding Handbook" in text
    assert "Laptop with charger | IT desk | Yes, on your last day" in text


def test_clean_text():
    assert clean_text("  ﬁle\n\n  name  ") == "file name"
