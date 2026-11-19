from pathlib import Path

import pymupdf

from app.services import vector_store

SAMPLES = Path(__file__).parent.parent / "samples"


def upload(client, file_name, data):
    return client.post("/documents", files={"file": (file_name, data)})


def sample(name):
    return (SAMPLES / name).read_bytes()


def test_upload_pdf(client):
    response = upload(client, "policy.pdf", sample("policy.pdf"))

    assert response.status_code == 201
    assert response.json()["id"] == "d1"
    assert response.json()["chunks"] > 0


def test_upload_docx(client):
    response = upload(client, "handbook.docx", sample("handbook.docx"))

    assert response.status_code == 201
    assert response.json()["id"] == "d1"


def test_each_document_gets_the_next_id(client):
    first = upload(client, "policy.pdf", sample("policy.pdf"))
    second = upload(client, "handbook.docx", sample("handbook.docx"))

    assert first.json()["id"] == "d1"
    assert second.json()["id"] == "d2"


def test_chunks_are_saved_with_the_file_name(client):
    response = upload(client, "policy.pdf", sample("policy.pdf"))

    saved = vector_store.collection.get(where={"doc_id": "d1"})
    assert len(saved["ids"]) == response.json()["chunks"]
    for metadata in saved["metadatas"]:
        assert metadata["file_name"] == "policy.pdf"
    assert {metadata["page"] for metadata in saved["metadatas"]} == {1, 2, 3}


def test_word_chunks_have_no_page(client):
    upload(client, "handbook.docx", sample("handbook.docx"))

    saved = vector_store.collection.get(where={"doc_id": "d1"})
    for metadata in saved["metadatas"]:
        assert "page" not in metadata


def test_png_is_rejected(client):
    response = upload(client, "image.png", sample("image.png"))
    assert response.status_code == 415


def test_renamed_png_is_rejected(client):
    response = upload(client, "image.pdf", sample("image.png"))
    assert response.status_code == 415


def test_empty_file_is_rejected(client):
    response = upload(client, "empty.pdf", b"")
    assert response.status_code == 400


def test_too_big_file_is_rejected(client, monkeypatch):
    monkeypatch.setattr("app.api.documents.MAX_FILE_SIZE_MB", 1)
    response = upload(client, "big.pdf", b"%PDF" + b"0" * (1024 * 1024))
    assert response.status_code == 413


def test_document_bigger_than_one_chroma_batch(client, monkeypatch):
    monkeypatch.setattr(vector_store, "MAX_BATCH_SIZE", 2)

    response = upload(client, "policy.pdf", sample("policy.pdf"))

    saved = vector_store.collection.get(where={"doc_id": "d1"})
    assert response.status_code == 201
    assert len(saved["ids"]) == response.json()["chunks"] > 2


def test_pdf_without_text_is_rejected(client):
    pdf = pymupdf.open()
    pdf.new_page()
    response = upload(client, "scan.pdf", pdf.tobytes())
    assert response.status_code == 422


def test_model_error_returns_503(client, monkeypatch):
    def broken_model(texts):
        raise RuntimeError("no internet")

    monkeypatch.setattr("app.api.documents.embed_texts", broken_model)
    response = upload(client, "policy.pdf", sample("policy.pdf"))
    assert response.status_code == 503


def test_list_documents(client):
    assert client.get("/documents").json() == []

    upload(client, "policy.pdf", sample("policy.pdf"))
    upload(client, "handbook.docx", sample("handbook.docx"))

    response = client.get("/documents")
    assert response.status_code == 200
    assert response.json() == [
        {"id": "d1", "name": "policy.pdf"},
        {"id": "d2", "name": "handbook.docx"},
    ]


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
