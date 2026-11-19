import io
import unicodedata

import pymupdf
from docx import Document


def read_pdf(data: bytes) -> list[str]:
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        return [clean_text(page.get_text()) for page in pdf]


def read_docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    lines = [paragraph.text for paragraph in doc.paragraphs]

    for table in doc.tables:
        for row in table.rows:
            lines.append(" | ".join(cell.text.strip() for cell in row.cells))

    return clean_text("\n".join(lines))


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return " ".join(text.split())
