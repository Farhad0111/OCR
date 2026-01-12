# API routes for Vector Database endpoints with Chunking

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import os
import openai
from dotenv import load_dotenv
from .VectorDB import VectorDBService
from .VectorDB_Schema import (
    AddDocumentResponse,
    ChunkInfo,
    QueryRequest,
    QueryResponse,
    QueryResult,
    DeleteDocumentRequest,
    DeleteDocumentResponse,
    ListCollectionsResponse,
    CollectionInfoResponse,
    QuestionAnswerRequest,
    QuestionAnswerResponse,
    SourceChunk
)

load_dotenv()

router = APIRouter(prefix="/vectordb", tags=["Vector Database"])

# Initialize OpenAI client
openai_client = None
if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_api_key_here":
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_answer_with_openai(query: str, chunks: list) -> str:
    """Generate an answer using OpenAI based on retrieved chunks."""
    if not openai_client:
        return None
    
    # Build context from chunks
    context = "\n\n".join([chunk.get("content", "") for chunk in chunks])
    
    if not context.strip():
        return "No relevant information found in the documents."
    
    try:
        response = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer the user's question based ONLY on the provided context. Be concise and direct. If the answer is not clearly found in the context, say 'I cannot find this information in the provided documents.'"
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}"
                }
            ],
            temperature=0.2,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating answer: {str(e)}"


@router.post("/add-document", response_model=AddDocumentResponse)
async def add_document(
    file: UploadFile = File(...),
    collection_name: str = Form(default="default"),
    chunk_size: int = Form(default=500, ge=100, le=5000),
    chunk_overlap: int = Form(default=50, ge=0, le=500)
):
    """
    Upload a document and add it to the vector database with chunking.
    
    Supports: .txt, .pdf, .docx files
    
    Args:
        file: Uploaded file (txt, pdf, or docx)
        collection_name: Name of the collection to store chunks
        chunk_size: Size of each text chunk in characters (100-5000)
        chunk_overlap: Overlap between consecutive chunks (0-500)
        
    Returns:
        AddDocumentResponse with chunk information
    """
    filename = file.filename or "unknown"
    
    # Read file content
    try:
        contents = await file.read()
        text = ""
        
        # Handle different file types
        if filename.endswith('.txt') or (file.content_type and file.content_type == "text/plain"):
            text = contents.decode('utf-8', errors='ignore')
            
        elif filename.endswith('.pdf') or (file.content_type and file.content_type == "application/pdf"):
            import fitz
            pdf_document = fitz.open(stream=contents, filetype="pdf")
            text_parts = []
            for page in pdf_document:
                text_parts.append(page.get_text())
            text = "\n".join(text_parts)
            pdf_document.close()
            
        elif filename.endswith('.docx'):
            from docx import Document
            from io import BytesIO
            doc = Document(BytesIO(contents))
            text_parts = [para.text for para in doc.paragraphs]
            text = "\n".join(text_parts)
            
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload .txt, .pdf, or .docx files."
            )
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text content found in the document.")
        
        # Add document to vector database with chunking
        total_chunks, chunk_infos = await VectorDBService.add_document(
            text=text,
            filename=filename,
            collection_name=collection_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        return AddDocumentResponse(
            filename=filename,
            collection_name=collection_name,
            total_chunks=total_chunks,
            chunks=[ChunkInfo(**chunk) for chunk in chunk_infos],
            success=True,
            message=f"Successfully added {total_chunks} chunks to collection '{collection_name}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query the vector database for similar document chunks.
    
    Args:
        request: QueryRequest with query text, collection name, and top_k
        
    Returns:
        QueryResponse with matching chunks, similarity scores, and AI-generated answer
    """
    try:
        results = await VectorDBService.query_documents(
            query=request.query,
            collection_name=request.collection_name,
            top_k=request.top_k
        )
        
        # Generate AI answer using OpenAI
        answer = generate_answer_with_openai(request.query, results)
        
        return QueryResponse(
            query=request.query,
            answer=answer,
            collection_name=request.collection_name,
            results=[QueryResult(**r) for r in results],
            total_results=len(results),
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.delete("/delete-document", response_model=DeleteDocumentResponse)
async def delete_document(request: DeleteDocumentRequest):
    """
    Delete documents from the vector database.
    
    Can delete by specific document ID or by filename (deletes all chunks).
    
    Args:
        request: DeleteDocumentRequest with collection name and document_id or filename
        
    Returns:
        DeleteDocumentResponse with deletion count
    """
    if not request.document_id and not request.filename:
        raise HTTPException(
            status_code=400,
            detail="Either document_id or filename must be provided"
        )
    
    try:
        deleted_count = await VectorDBService.delete_document(
            collection_name=request.collection_name,
            document_id=request.document_id,
            filename=request.filename
        )
        
        return DeleteDocumentResponse(
            collection_name=request.collection_name,
            deleted_count=deleted_count,
            success=deleted_count > 0,
            message=f"Deleted {deleted_count} document(s) from collection '{request.collection_name}'"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/collections", response_model=ListCollectionsResponse)
async def list_collections():
    """
    List all collections in the vector database.
    
    Returns:
        ListCollectionsResponse with list of collection names
    """
    try:
        collections = await VectorDBService.list_collections()
        
        return ListCollectionsResponse(
            collections=collections,
            total_collections=len(collections),
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.post("/ask", response_model=QuestionAnswerResponse)
async def ask_question(request: QuestionAnswerRequest):
    """
    Ask a question and get an answer based on stored documents.
    
    The system searches for relevant information in the vector database.
    If relevant content is found, it returns an answer based on that content.
    If no relevant information is found, it returns a message indicating no related information is available.
    
    Args:
        request: QuestionAnswerRequest with question, collection name, top_k, and similarity threshold
        
    Returns:
        QuestionAnswerResponse with answer and source information
    """
    try:
        result = await VectorDBService.answer_question(
            question=request.question,
            collection_name=request.collection_name,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        return QuestionAnswerResponse(
            question=request.question,
            answer=result["answer"],
            has_answer=result["has_answer"],
            sources=[SourceChunk(**s) for s in result["sources"]],
            collection_name=request.collection_name,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")
