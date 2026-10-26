
import io

import pytest
from fastapi.testclient import TestClient

from backend.main import app, document_store


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_document_store():
    """Reset the in-memory document store before every test."""
    document_store["chunks"] = []
    document_store["index"] = None
    document_store["filename"] = None

    yield

    document_store["chunks"] = []
    document_store["index"] = None
    document_store["filename"] = None


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to DocuMind AI!",
        "status": "running",
    }


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_chat_without_uploaded_pdf():
    response = client.post(
        "/chat",
        json={"question": "What is this document about?"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Please upload a PDF before asking questions."
    )


def test_chat_with_empty_question(monkeypatch):
    document_store["chunks"] = ["Example document content"]
    document_store["index"] = object()
    document_store["filename"] = "sample.pdf"

    response = client.post(
        "/chat",
        json={"question": "   "},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty."


def test_chat_success(monkeypatch):
    document_store["chunks"] = ["DocuMind AI is a PDF chatbot."]
    document_store["index"] = object()
    document_store["filename"] = "sample.pdf"

    def fake_search(**kwargs):
        assert kwargs["question"] == "What is DocuMind AI?"
        assert kwargs["top_k"] == 3

        return [
            {
                "text": "DocuMind AI is a PDF chatbot.",
                "similarity": 0.95,
            }
        ]

    def fake_generate_answer(question, relevant_chunks):
        assert question == "What is DocuMind AI?"
        assert len(relevant_chunks) == 1

        return "DocuMind AI answers questions about PDFs."

    monkeypatch.setattr(
        "backend.main.search_similar_chunks",
        fake_search,
    )
    monkeypatch.setattr(
        "backend.main.generate_answer",
        fake_generate_answer,
    )

    response = client.post(
        "/chat",
        json={"question": "  What is DocuMind AI?  "},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["question"] == "What is DocuMind AI?"
    assert data["answer"] == (
        "DocuMind AI answers questions about PDFs."
    )
    assert data["source_document"] == "sample.pdf"
    assert len(data["sources"]) == 1


def test_chat_when_no_relevant_chunks_found(monkeypatch):
    document_store["chunks"] = ["Example document content"]
    document_store["index"] = object()
    document_store["filename"] = "sample.pdf"

    monkeypatch.setattr(
        "backend.main.search_similar_chunks",
        lambda **kwargs: [],
    )

    response = client.post(
        "/chat",
        json={"question": "An unrelated question"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "No relevant information was found."
    )


def test_upload_rejects_non_pdf():
    response = client.post(
        "/upload",
        files={
            "file": (
                "notes.txt",
                io.BytesIO(b"This is a text file."),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Please upload a PDF file."


def test_upload_success(monkeypatch):
    def fake_extract_text(file_path):
        return "DocuMind AI processes PDF documents."

    def fake_split_text(text, chunk_size, chunk_overlap):
        return ["DocuMind AI processes PDF documents."]

    def fake_create_index(chunks):
        return object()

    monkeypatch.setattr(
        "backend.main.extract_text_from_pdf",
        fake_extract_text,
    )
    monkeypatch.setattr(
        "backend.main.split_text_into_chunks",
        fake_split_text,
    )
    monkeypatch.setattr(
        "backend.main.create_vector_index",
        fake_create_index,
    )

    response = client.post(
        "/upload",
        files={
            "file": (
                "sample.pdf",
                io.BytesIO(b"Mock PDF content"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "sample.pdf"
    assert data["total_chunks"] == 1
    assert document_store["chunks"] == [
        "DocuMind AI processes PDF documents."
    ]
    assert document_store["filename"] == "sample.pdf"
    assert document_store["index"] is not None


def test_upload_rejects_pdf_without_readable_text(monkeypatch):
    monkeypatch.setattr(
        "backend.main.extract_text_from_pdf",
        lambda file_path: "",
    )

    response = client.post(
        "/upload",
        files={
            "file": (
                "blank.pdf",
                io.BytesIO(b"Mock PDF content"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "No readable text was found in this PDF."
    )


def test_upload_handles_processing_error(monkeypatch):
    def fake_extract_text(file_path):
        raise RuntimeError("Simulated processing failure")

    monkeypatch.setattr(
        "backend.main.extract_text_from_pdf",
        fake_extract_text,
    )

    response = client.post(
        "/upload",
        files={
            "file": (
                "sample.pdf",
                io.BytesIO(b"Mock PDF content"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "An error occurred while processing the PDF."
    )
