from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

model = DefaultEmbeddingFunction()


def embed_texts(texts: list[str]):
    return model(texts)
