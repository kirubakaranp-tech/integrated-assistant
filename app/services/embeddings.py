from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

# Chroma's default model (all-MiniLM-L6-v2). It runs on your own computer, so
# no API key is needed. It is downloaded the first time it is used (~80 MB).
model = DefaultEmbeddingFunction()


def embed_texts(texts: list[str]):
    """Turn each text into a vector of 384 numbers."""
    return model(texts)
