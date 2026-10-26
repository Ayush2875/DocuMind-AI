def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Extracted PDF text.
        chunk_size: Maximum number of characters per chunk.
        chunk_overlap: Number of characters shared between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be non-negative and smaller than chunk_size"
        )

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)
    step = chunk_size - chunk_overlap

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += step

    return chunks