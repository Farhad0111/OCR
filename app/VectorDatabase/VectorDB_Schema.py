# Pydantic schemas for Vector Database endpoints

from pydantic import BaseModel, Field
from typing import List, Optional


class ChunkInfo(BaseModel):
    """Information about a single chunk."""
    chunk_id: str
    chunk_index: int
    content: str
    start_char: int
    end_char: int
    metadata: dict = {}


class AddDocumentRequest(BaseModel):
    """Request schema for adding a document with chunking."""
    collection_name: str = Field(default="default", description="Name of the collection to store documents")
    chunk_size: int = Field(default=500, ge=100, le=5000, description="Size of each text chunk in characters")
    chunk_overlap: int = Field(default=50, ge=0, le=500, description="Overlap between consecutive chunks")


class AddDocumentResponse(BaseModel):
    """Response schema for adding a document."""
    filename: str
    collection_name: str
    total_chunks: int
    chunks: List[ChunkInfo]
    success: bool
    message: str


class QueryRequest(BaseModel):
    """Request schema for querying the vector database."""
    query: str = Field(..., description="The search query text")
    collection_name: str = Field(default="default", description="Name of the collection to search")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top results to return")


class QueryResult(BaseModel):
    """A single query result."""
    chunk_id: str
    content: str
    score: float
    metadata: dict = {}


class QueryResponse(BaseModel):
    """Response schema for querying the vector database."""
    query: str
    answer: Optional[str] = None  # AI-generated answer
    answer_source: Optional[str] = None  # 'document', 'gpt', or None
    found_in_docs: bool = True  # Whether answer was found in documents
    collection_name: str
    results: List[QueryResult]
    total_results: int
    success: bool


class DeleteDocumentRequest(BaseModel):
    """Request schema for deleting a document."""
    collection_name: str = Field(default="default", description="Name of the collection")
    document_id: Optional[str] = Field(None, description="Specific document ID to delete")
    filename: Optional[str] = Field(None, description="Filename to delete all chunks for")


class DeleteDocumentResponse(BaseModel):
    """Response schema for deleting a document."""
    collection_name: str
    deleted_count: int
    success: bool
    message: str


class DocumentInfo(BaseModel):
    """Information about a document in a collection."""
    document_id: str
    filename: str


class CollectionDetail(BaseModel):
    """Detailed information about a collection."""
    collection_name: str
    documents: List[DocumentInfo]


class ListCollectionsResponse(BaseModel):
    """Response schema for listing collections."""
    collections: List[CollectionDetail]
    total_collections: int
    success: bool


class CollectionInfoResponse(BaseModel):
    """Response schema for collection information."""
    collection_name: str
    document_count: int
    success: bool
    message: str


class QuestionAnswerRequest(BaseModel):
    """Request schema for question answering."""
    question: str = Field(..., description="The question to answer")
    collection_name: str = Field(default="default", description="Name of the collection to search")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of relevant chunks to consider")
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum similarity score to consider relevant")


class SourceChunk(BaseModel):
    """Source chunk used for answering."""
    content: str
    filename: str
    score: float


class QuestionAnswerResponse(BaseModel):
    """Response schema for question answering."""
    question: str
    answer: str
    has_answer: bool
    sources: List[SourceChunk]
    collection_name: str
    success: bool
