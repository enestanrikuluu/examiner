from src.ai.rag.chunker import chunk_text, estimate_tokens


def test_chunk_short_text_returns_single_chunk() -> None:
    text = "This is a short text."
    chunks = chunk_text(text, chunk_size=500)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_empty_text_returns_empty() -> None:
    chunks = chunk_text("", chunk_size=500)
    assert chunks == []


def test_chunk_splits_long_text() -> None:
    paragraphs = ["Paragraph " + str(i) + ". " * 20 for i in range(20)]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    # All chunks should be non-empty
    for chunk in chunks:
        assert len(chunk.strip()) > 0


def test_chunk_respects_max_size() -> None:
    text = "word " * 500
    chunks = chunk_text(text, chunk_size=100, chunk_overlap=10)
    # Most chunks should be near the size limit
    for chunk in chunks:
        assert len(chunk) <= 200  # Allow some tolerance


def test_estimate_tokens_reasonable() -> None:
    text = "Hello world, this is a test."
    tokens = estimate_tokens(text)
    assert 3 <= tokens <= 15


def test_estimate_tokens_empty() -> None:
    assert estimate_tokens("") == 1  # minimum 1
