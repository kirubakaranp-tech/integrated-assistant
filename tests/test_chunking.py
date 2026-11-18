from app.services.chunking import split_text


def test_short_text_is_one_chunk():
    assert split_text("Hello world", chunk_size=100, overlap=10) == ["Hello world"]


def test_empty_text_has_no_chunks():
    assert split_text("   ", chunk_size=100, overlap=10) == []


def test_chunks_are_not_too_long():
    chunks = split_text("word " * 1000, chunk_size=100, overlap=20)
    for chunk in chunks:
        assert len(chunk) <= 100


def test_next_chunk_repeats_the_end_of_the_previous_one():
    text = " ".join(f"word{i}" for i in range(200))
    chunks = split_text(text, chunk_size=60, overlap=20)

    for i in range(len(chunks) - 1):
        last_word = chunks[i].split()[-1]
        assert last_word in chunks[i + 1].split()


def test_no_words_are_lost():
    words = [f"word{i}" for i in range(200)]
    chunks = split_text(" ".join(words), chunk_size=60, overlap=20)

    words_in_chunks = " ".join(chunks).split()
    for word in words:
        assert word in words_in_chunks


def test_very_long_word_gets_its_own_chunk():
    long_word = "x" * 150
    chunks = split_text(f"start {long_word} end", chunk_size=100, overlap=20)
    assert chunks == ["start", long_word, "end"]
