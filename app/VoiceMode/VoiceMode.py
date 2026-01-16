# Service logic for Voice Mode operations (STT + RAG)

import os
from typing import Tuple, List
from dotenv import load_dotenv

load_dotenv()

class VoiceModeService:
    """Service class for Voice Mode operations with STT and RAG."""
    
    @staticmethod
    async def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
        """
        Transcribe audio to text using OpenAI Whisper.
        
        Args:
            audio_bytes: The audio file bytes
            filename: Name of the audio file
            
        Returns:
            Transcribed text string
        """
        import openai
        from io import BytesIO
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError("OPENAI_API_KEY not configured in .env file")
        
        client = openai.OpenAI(api_key=api_key)
        
        try:
            # Create a file-like object from bytes
            audio_file = BytesIO(audio_bytes)
            audio_file.name = filename
            
            # Transcribe using Whisper
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            
            return transcript.strip()
            
        except Exception as e:
            raise Exception(f"Audio transcription failed: {str(e)}")
    
    
    @staticmethod
    async def generate_answer_with_rag(
        query: str, 
        chunks: List[dict], 
        fallback_to_gpt: bool = True
    ) -> dict:
        """
        Generate an answer using OpenAI based on retrieved chunks.
        If no relevant content found and fallback_to_gpt is True, answer directly from GPT.
        
        Args:
            query: The search query
            chunks: Retrieved document chunks
            fallback_to_gpt: Whether to fallback to GPT if no relevant docs found
            
        Returns:
            dict with 'answer', 'source' ('document' or 'gpt')
        """
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            return {
                "answer": "OpenAI API key not configured. Cannot generate answer.",
                "source": "error"
            }
        
        client = openai.OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Build context from chunks
        context = "\n\n".join([chunk.get("content", "") for chunk in chunks])
        
        # Check if we have meaningful content from documents
        if not context.strip() or len(chunks) == 0:
            if fallback_to_gpt:
                # No document content found, fallback to GPT direct answer
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful assistant. Answer the user's question to the best of your knowledge. Be concise and informative."
                            },
                            {
                                "role": "user",
                                "content": query
                            }
                        ],
                        temperature=0.7,
                        max_tokens=500
                    )
                    return {
                        "answer": response.choices[0].message.content,
                        "source": "gpt"
                    }
                except Exception as e:
                    return {
                        "answer": f"Error generating answer: {str(e)}",
                        "source": "error"
                    }
            else:
                return {
                    "answer": "No relevant information found in the documents.",
                    "source": "none"
                }
        
        # We have document content, try to answer from it
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful assistant. Answer the user's question based on the provided context. 
Be concise and direct. If the answer is clearly found in the context, provide it.
If the context does not contain relevant information to answer the question, respond with exactly: "NOT_FOUND_IN_DOCS" """
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}"
                    }
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            # Check if GPT couldn't find the answer in documents
            if "NOT_FOUND_IN_DOCS" in answer and fallback_to_gpt:
                # Fallback to GPT direct answer
                fallback_response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant. Answer the user's question to the best of your knowledge. Be concise and informative."
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return {
                    "answer": fallback_response.choices[0].message.content,
                    "source": "gpt"
                }
            
            return {
                "answer": answer,
                "source": "document"
            }
            
        except Exception as e:
            return {
                "answer": f"Error generating answer: {str(e)}",
                "source": "error"
            }

