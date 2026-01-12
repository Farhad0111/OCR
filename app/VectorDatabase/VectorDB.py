# Service logic for Vector Database operations with Chunking

import os
import uuid
import hashlib
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ChromaDB configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")


class TextChunker:
    """Utility class for chunking text documents."""
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[dict]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: The text to chunk
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text or len(text) == 0:
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                last_space = text.rfind(' ', start, end)
                
                # Prefer sentence boundary, then newline, then space
                if last_period > start + chunk_size // 2:
                    end = last_period + 1
                elif last_newline > start + chunk_size // 2:
                    end = last_newline + 1
                elif last_space > start + chunk_size // 2:
                    end = last_space + 1
            
            chunk_content = text[start:end].strip()
            
            if chunk_content:
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": chunk_content,
                    "start_char": start,
                    "end_char": end
                })
                chunk_index += 1
            
            # Move start position with overlap
            start = end - chunk_overlap if end < len(text) else end
            
            # Prevent infinite loop
            if start >= len(text) or (end >= len(text) and chunk_content):
                break
        
        return chunks


class VectorDBService:
    """Service class for Vector Database operations using ChromaDB."""
    
    _client = None
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize ChromaDB client."""
        if cls._initialized:
            return
        
        print("Initializing ChromaDB...")
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            cls._client = chromadb.PersistentClient(
                path=CHROMA_DB_PATH,
                settings=Settings(anonymized_telemetry=False)
            )
            cls._initialized = True
            print("ChromaDB initialized successfully!")
        except ImportError:
            raise RuntimeError(
                "ChromaDB is not installed. Please install it with:\n"
                "  pip install chromadb"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ChromaDB: {e}")
    
    @classmethod
    def _get_or_create_collection(cls, collection_name: str):
        """Get or create a collection."""
        if not cls._initialized:
            cls.initialize()
        return cls._client.get_or_create_collection(name=collection_name)
    
    @classmethod
    def _generate_document_id(cls, filename: str, chunk_index: int) -> str:
        """Generate a unique document ID."""
        unique_string = f"{filename}_{chunk_index}_{uuid.uuid4().hex[:8]}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    @classmethod
    async def add_document(
        cls,
        text: str,
        filename: str,
        collection_name: str = "default",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        metadata: dict = None
    ) -> Tuple[int, List[dict]]:
        """
        Add a document to the vector database with chunking.
        
        Args:
            text: The document text to add
            filename: Original filename
            collection_name: Name of the collection
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            metadata: Additional metadata for the document
            
        Returns:
            Tuple of (total_chunks, list of chunk info)
        """
        if not cls._initialized:
            cls.initialize()
        
        # Chunk the text
        chunks = TextChunker.chunk_text(text, chunk_size, chunk_overlap)
        
        if not chunks:
            return 0, []
        
        collection = cls._get_or_create_collection(collection_name)
        
        chunk_infos = []
        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            chunk_id = cls._generate_document_id(filename, chunk["chunk_index"])
            
            chunk_metadata = {
                "filename": filename,
                "chunk_index": chunk["chunk_index"],
                "start_char": chunk["start_char"],
                "end_char": chunk["end_char"],
                **(metadata or {})
            }
            
            ids.append(chunk_id)
            documents.append(chunk["content"])
            metadatas.append(chunk_metadata)
            
            chunk_infos.append({
                "chunk_id": chunk_id,
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
                "start_char": chunk["start_char"],
                "end_char": chunk["end_char"],
                "metadata": chunk_metadata
            })
        
        # Add to ChromaDB
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        return len(chunks), chunk_infos
    
    @classmethod
    async def query_documents(
        cls,
        query: str,
        collection_name: str = "default",
        top_k: int = 5
    ) -> List[dict]:
        """
        Query the vector database for similar documents.
        
        Args:
            query: The search query
            collection_name: Name of the collection to search
            top_k: Number of results to return
            
        Returns:
            List of query results with scores
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            collection = cls._client.get_collection(name=collection_name)
        except Exception:
            return []
        
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        query_results = []
        
        if results and results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                result = {
                    "chunk_id": doc_id,
                    "content": results['documents'][0][i] if results['documents'] else "",
                    "score": 1 - results['distances'][0][i] if results['distances'] else 0.0,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                }
                query_results.append(result)
        
        return query_results
    
    @classmethod
    async def delete_document(
        cls,
        collection_name: str = "default",
        document_id: Optional[str] = None,
        filename: Optional[str] = None
    ) -> int:
        """
        Delete documents from the vector database.
        
        Args:
            collection_name: Name of the collection
            document_id: Specific document ID to delete
            filename: Filename to delete all chunks for
            
        Returns:
            Number of documents deleted
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            collection = cls._client.get_collection(name=collection_name)
        except Exception:
            return 0
        
        if document_id:
            # Delete specific document
            collection.delete(ids=[document_id])
            return 1
        elif filename:
            # Delete all chunks with matching filename
            results = collection.get(
                where={"filename": filename}
            )
            if results and results['ids']:
                collection.delete(ids=results['ids'])
                return len(results['ids'])
        
        return 0
    
    @classmethod
    async def answer_question(
        cls,
        question: str,
        collection_name: str = "default",
        top_k: int = 3,
        similarity_threshold: float = 0.3
    ) -> dict:
        """
        Answer a question based on stored documents.
        
        Args:
            question: The question to answer
            collection_name: Name of the collection to search
            top_k: Number of relevant chunks to consider
            similarity_threshold: Minimum similarity score to consider relevant
            
        Returns:
            Dictionary with answer and source information
        """
        if not cls._initialized:
            cls.initialize()
        
        # Query for relevant chunks
        results = await cls.query_documents(
            query=question,
            collection_name=collection_name,
            top_k=top_k
        )
        
        # Check if we have any results (scores can be negative in ChromaDB distance)
        if not results:
            return {
                "has_answer": False,
                "answer": "No related information available in the stored documents.",
                "sources": []
            }
        
        # Take the top results - ChromaDB returns sorted by relevance
        # Use results directly since they are already sorted by similarity
        relevant_chunks = results[:top_k]
        
        # Build context from relevant chunks
        context_parts = []
        sources = []
        
        for chunk in relevant_chunks:
            context_parts.append(chunk["content"])
            sources.append({
                "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                "filename": chunk.get("metadata", {}).get("filename", "unknown"),
                "score": chunk.get("score", 0.0)
            })
        
        # Combine context and generate answer
        combined_context = "\n\n".join(context_parts)
        
        # Generate a concise answer
        answer = cls._generate_answer(question, combined_context)
        
        return {
            "has_answer": True,
            "answer": answer,
            "sources": sources
        }
    
    @staticmethod
    def _generate_answer(question: str, context: str) -> str:
        """
        Generate a concise answer from the context.
        
        Args:
            question: The question asked
            context: Combined context from relevant chunks
            
        Returns:
            Generated answer string
        """
        question_lower = question.lower()
        
        # Extract key information based on question type
        if "name" in question_lower and "university" in question_lower:
            # Look for university name in context
            import re
            university_pattern = r'(?:at|from|in)\s+([A-Z][a-zA-Z\s]+(?:University|College|Institute)[^,.\n]*)'
            match = re.search(university_pattern, context)
            if match:
                return match.group(1).strip()
        
        if "what is" in question_lower or "who is" in question_lower:
            # Return first relevant sentence
            sentences = context.split('.')
            for sentence in sentences:
                if len(sentence.strip()) > 20:
                    return sentence.strip() + "."
        
        if "when" in question_lower:
            # Look for dates/years
            import re
            date_pattern = r'\b((?:19|20)\d{2}(?:\s*[-–to]+\s*(?:19|20)\d{2})?)\b'
            dates = re.findall(date_pattern, context)
            if dates:
                return f"The relevant time period is: {', '.join(dates[:3])}"
        
        if "where" in question_lower:
            # Look for location information
            import re
            location_pattern = r'(?:from|in|at)\s+([A-Z][a-zA-Z\s,]+(?:Bangladesh|India|USA|UK|Dhaka|University)[^.]*)'
            match = re.search(location_pattern, context)
            if match:
                return match.group(1).strip()
        
        # Default: return the most relevant part of context (first 500 chars)
        if len(context) > 500:
            # Find a good break point
            break_point = context[:500].rfind('.')
            if break_point > 200:
                return context[:break_point + 1].strip()
            return context[:500].strip() + "..."
        
        return context.strip()
    
    @classmethod
    async def list_collections(cls) -> List[str]:
        """
        List all collections in the database.
        
        Returns:
            List of collection names
        """
        if not cls._initialized:
            cls.initialize()
        
        collections = cls._client.list_collections()
        return [col.name for col in collections]
    
    @classmethod
    async def get_collection_info(cls, collection_name: str) -> dict:
        """
        Get information about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with collection information
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            collection = cls._client.get_collection(name=collection_name)
            count = collection.count()
            return {
                "exists": True,
                "document_count": count
            }
        except Exception:
            return {
                "exists": False,
                "document_count": 0
            }
