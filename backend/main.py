
import os
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.pdf_processor import extract_text_from_pdf
from backend.text_chunker import split_text_into_chunks
from backend.vector_store import create_vector_index, search_similar_chunks

from pydantic import BaseModel
from backend.vector_store import search_similar_chunks
from backend.answer_generator import generate_answer

app = FastAPI(title="DocuMind AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary in-memory storage for the currently uploaded PDF
document_store = {
    "chunks": [],
    "index": None,
    "filename": None,
}

class ChatRequest(BaseModel):
    question: str

@app.get("/")
def home():
    return {
        "message": "Welcome to DocuMind AI!",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file."
        )

    temporary_path = None

    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temporary_file:
            temporary_file.write(await file.read())
            temporary_path = temporary_file.name

        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(temporary_path)

        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="No readable text was found in this PDF."
            )

        # Divide the text into smaller chunks
        chunks = split_text_into_chunks(
            extracted_text,
            chunk_size=1000,
            chunk_overlap=200
        )

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not create text chunks from this PDF."
            )

        # Generate embeddings and create the FAISS index
        index = create_vector_index(chunks)

        # Save the processed document in memory
        document_store["chunks"] = chunks
        document_store["index"] = index
        document_store["filename"] = file.filename

        return {
            "message": "PDF uploaded and processed successfully!",
            "filename": file.filename,
            "total_chunks": len(chunks)
        }

    except HTTPException:
        raise

    except Exception as error:
        print(f"PDF processing error: {error}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the PDF."
        )

    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


@app.post("/chat")
def chat_with_pdf(request: ChatRequest):
    # Check whether a PDF has been uploaded
    if document_store["index"] is None:
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF before asking questions."
        )

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        # Find the three most relevant chunks
        relevant_chunks = search_similar_chunks(
            question=question,
            chunks=document_store["chunks"],
            index=document_store["index"],
            top_k=3
        )

        if not relevant_chunks:
            raise HTTPException(
                status_code=404,
                detail="No relevant information was found."
            )

        # Generate an answer using the retrieved context
        answer = generate_answer(question, relevant_chunks)

        return {
            "question": question,
            "answer": answer,
            "source_document": document_store["filename"],
            "sources": relevant_chunks
        }

    except HTTPException:
        raise

    except Exception as error:
        print(f"Chat error: {error}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while answering your question."
        )
