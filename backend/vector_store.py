import os

import faiss
import numpy as np
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing. Add it to your .env file."
    )

client = genai.Client(api_key=API_KEY)

# Embedding model used for both document chunks and questions.
EMBEDDING_MODEL = "gemini-embedding-001"


def generate_embeddings(texts: list[str]) -> np.ndarray:
    """
    Convert a list of text strings into normalized embedding vectors.
    """
    if not texts:
        raise ValueError("Cannot generate embeddings for empty text.")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config={
            "task_type": "RETRIEVAL_DOCUMENT",
            "output_dimensionality": 768,
        },
    )

    vectors = np.array(
        [item.values for item in response.embeddings],
        dtype=np.float32,
    )

    # Normalize vectors so inner-product search measures cosine similarity.
    faiss.normalize_L2(vectors)

    return vectors


def create_vector_index(chunks: list[str]):
    """
    Create a FAISS index from document chunks.
    """
    if not chunks:
        raise ValueError("Cannot create a vector index without text chunks.")

    vectors = generate_embeddings(chunks)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    return index


def search_similar_chunks(
    question: str,
    chunks: list[str],
    index,
    top_k: int = 3,
) -> list[dict]:
    """
    Return the most relevant chunks for a user's question.
    """
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if not chunks:
        return []

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config={
            "task_type": "RETRIEVAL_QUERY",
            "output_dimensionality": 768,
        },
    )

    question_vector = np.array(
        [response.embeddings[0].values],
        dtype=np.float32,
    )

    faiss.normalize_L2(question_vector)

    scores, indices = index.search(
        question_vector,
        min(top_k, len(chunks)),
    )

    results = []

    for score, chunk_index in zip(scores[0], indices[0]):
        if chunk_index >= 0:
            results.append({
                "text": chunks[int(chunk_index)],
                "similarity": float(score),
            })

    return results