import threading

import chromadb
from chromadb.config import Settings

from app.config import CHROMA_DIR, COLLECTION_NAME

client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
collection = client.get_or_create_collection(COLLECTION_NAME)
MAX_BATCH_SIZE = client.get_max_batch_size()

save_lock = threading.Lock()


def save_document(file_name: str, chunks: list[str], embeddings, page_numbers: list) -> str:
    with save_lock:
        doc_id = f"d{len(list_documents()) + 1}"

        ids = []
        metadatas = []
        for i in range(len(chunks)):
            ids.append(f"{doc_id}-{i}")
            metadata = {"doc_id": doc_id, "file_name": file_name, "chunk_index": i}
            if page_numbers[i] is not None:
                metadata["page"] = page_numbers[i]
            metadatas.append(metadata)

        for start in range(0, len(ids), MAX_BATCH_SIZE):
            end = start + MAX_BATCH_SIZE
            collection.add(
                ids=ids[start:end],
                documents=chunks[start:end],
                embeddings=embeddings[start:end],
                metadatas=metadatas[start:end],
            )

    return doc_id


def list_documents() -> list[dict]:
    result = collection.get(where={"chunk_index": 0}, include=["metadatas"])
    documents = [{"id": meta["doc_id"], "name": meta["file_name"]} for meta in result["metadatas"]]
    return sorted(documents, key=lambda doc: int(doc["id"][1:]))


def search(query_embedding, top_k: int) -> list[dict]:
    count = collection.count()
    if count == 0:
        return []

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for text, meta, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        chunks.append({"text": text, "file": meta["file_name"], "page": meta.get("page"), "distance": distance})
    return chunks
