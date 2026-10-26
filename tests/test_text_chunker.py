
import pytest

from backend.text_chunker import split_text_into_chunks


def test_empty_text_returns_empty_list():
    result = split_text_into_chunks("")

    assert result == []


def test_whitespace_returns_empty_list():
    result = split_text_into_chunks("   \n\t  ")

    assert result == []


def test_short_text_returns_one_chunk():
    text = "DocuMind AI processes PDF documents."

    result = split_text_into_chunks(text)

    assert result == [text]



def test_long_text_is_split_into_multiple_chunks():
    text = "A" * 2500

    result = split_text_into_chunks(
        text,
        chunk_size=1000,
        chunk_overlap=200
    )

    assert len(result) == 4
    assert all(len(chunk) <= 1000 for chunk in result)
    assert len("".join(result)) > len(text)
    assert len(result[-1]) == 100



def test_adjacent_chunks_have_overlap():
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 5

    result = split_text_into_chunks(
        text,
        chunk_size=50,
        chunk_overlap=10
    )

    assert len(result) > 1
    assert result[0][-10:] == result[1][:10]


def test_invalid_chunk_size_raises_error():
    with pytest.raises(ValueError):
        split_text_into_chunks(
            "Sample text",
            chunk_size=0
        )


def test_invalid_overlap_raises_error():
    with pytest.raises(ValueError):
        split_text_into_chunks(
            "Sample text",
            chunk_size=100,
            chunk_overlap=100
        )
