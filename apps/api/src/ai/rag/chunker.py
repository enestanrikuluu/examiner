"""Recursive text splitter for chunking documents."""

from __future__ import annotations


def chunk_text(
    text: str,
    *,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separators: list[str] | None = None,
) -> list[str]:
    """Split text into overlapping chunks.

    Uses a recursive approach: tries to split on paragraph breaks first,
    then sentence breaks, then word breaks.
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " "]

    if len(text) <= chunk_size:
        stripped = text.strip()
        return [stripped] if stripped else []

    # Find the best separator
    separator = separators[-1]
    for sep in separators:
        if sep in text:
            separator = sep
            break

    parts = text.split(separator)
    chunks: list[str] = []
    current_chunk = ""

    for part in parts:
        candidate = (
            current_chunk + separator + part if current_chunk else part
        )
        if len(candidate) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Overlap: keep the tail of the previous chunk
            if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                overlap_text = current_chunk[-chunk_overlap:]
                current_chunk = overlap_text + separator + part
            else:
                current_chunk = part
        else:
            current_chunk = candidate

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Recursively split any chunk that's still too large
    result: list[str] = []
    remaining_seps = (
        separators[separators.index(separator) + 1 :]
        if separator in separators
        else []
    )
    for chunk in chunks:
        if len(chunk) > chunk_size and remaining_seps:
            result.extend(
                chunk_text(
                    chunk,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=remaining_seps,
                )
            )
        else:
            result.append(chunk)

    return result


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token for Turkish/English."""
    return max(1, len(text) // 4)
