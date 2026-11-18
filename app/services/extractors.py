import io
import unicodedata

import pymupdf
from docx import Document


def read_pdf(data: bytes) -> list[str]:
    """Return the text of every page, so we can remember the page number of each chunk."""
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        return [clean_text(page.get_text()) for page in pdf]


def read_docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    lines = [paragraph.text for paragraph in doc.paragraphs]

    # tables are not part of doc.paragraphs, so read them row by row
    for table in doc.tables:
        for row in table.rows:
            lines.append(" | ".join(cell.text.strip() for cell in row.cells))

    return clean_text("\n".join(lines))


def clean_text(text: str) -> str:
    # PDFs often use ligatures like "ﬁ" - NFKC turns them back into normal letters
    text = unicodedata.normalize("NFKC", text)
    # remove extra spaces and line breaks
    return " ".join(text.split())
