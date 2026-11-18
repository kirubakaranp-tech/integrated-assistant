import threading

import chromadb
from chromadb.config import Settings

from app.config import CHROMA_DIR, COLLECTION_NAME

client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
collection = client.get_or_create_collection(COLLECTION_NAME)

# only one upload can save at a time, so two files never get the same id
save_lock = threading.Lock()


def save_document(file_name: str, chunks: list[str], embeddings, page_numbers: list) -> str:
    """Save the chunks of one document and return its new id (d1, d2, ...)."""
    with save_lock:
        doc_id = f"d{len(list_documents()) + 1}"

        ids = []
        metadatas = []
        for i in range(len(chunks)):
            ids.append(f"{doc_id}-{i}")
            metadata = {"doc_id": doc_id, "file_name": file_name, "chunk_index": i}
            if page_numbers[i] is not None:  # Word files have no page numbers
                metadata["page"] = page_numbers[i]
            metadatas.append(metadata)

        collection.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)

    return doc_id


def list_documents() -> list[dict]:
    # Every document has exactly one chunk with chunk_index 0,
    # so those chunks give us the list of documents.
    result = collection.get(where={"chunk_index": 0}, include=["metadatas"])
    documents = [{"id": meta["doc_id"], "name": meta["file_name"]} for meta in result["metadatas"]]
    return sorted(documents, key=lambda doc: int(doc["id"][1:]))  # d1, d2, ... d10 in the right order


def search(query_embedding, top_k: int) -> list[dict]:
    """Find the chunks closest to the question. A smaller distance means more similar."""
    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    # [0] because we asked with one question
    for text, meta, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        chunks.append({"text": text, "file": meta["file_name"], "page": meta.get("page"), "distance": distance})
    return chunks
