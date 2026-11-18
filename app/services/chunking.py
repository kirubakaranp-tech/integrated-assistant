from app.config import CHUNK_OVERLAP, CHUNK_SIZE


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into chunks of about chunk_size characters.

    Words are never cut in half. Each chunk starts with the last few words of
    the previous chunk (about `overlap` characters), so a sentence that falls
    on the border between two chunks is not lost.
    """
    chunks = []
    current = []  # words of the chunk we are building

    for word in text.split():
        if current and len(" ".join(current + [word])) > chunk_size:
            chunks.append(" ".join(current))
            current = last_words(current, overlap)
            # very long word: the overlap doesn't fit, so start an empty chunk
            if len(" ".join(current + [word])) > chunk_size:
                current = []
        current.append(word)

    if current:
        chunks.append(" ".join(current))
    return chunks


def last_words(words: list[str], max_length: int) -> list[str]:
    """Return the words from the end of the list that fit in max_length characters."""
    result = []
    for word in reversed(words):
        if len(" ".join([word] + result)) > max_length:
            break
        result.insert(0, word)
    return result
