# Service logic for OCR processing using EasyOCR (CPU-friendly)

import os
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from typing import Tuple
import numpy as np

# Load environment variables
load_dotenv()


class OCRService:
    """Service class for OCR operations using EasyOCR."""
    
    _reader = None
    _initialized = False
    
    @classmethod
    def initialize_model(cls):
        """Initialize EasyOCR reader."""
        if cls._initialized:
            return
        
        print("Initializing EasyOCR (this may take a moment on first run)...")
        
        try:
            import easyocr
            cls._reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            cls._initialized = True
            print("EasyOCR initialized successfully!")
        except ImportError:
            raise RuntimeError(
                "EasyOCR is not installed. Please install it with:\n"
                "  pip install easyocr"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize EasyOCR: {e}")

    @staticmethod
    async def _extract_text(image_bytes: bytes) -> str:
        """
        Extract text from an image using EasyOCR.
        
        Args:
            image_bytes: Raw bytes of the image file.
            
        Returns:
            Extracted text from the image.
        """
        if OCRService._reader is None:
            OCRService.initialize_model()
        
        # Convert bytes to numpy array
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)
        
        # Run OCR
        results = OCRService._reader.readtext(image_np)
        
        # Extract text from results
        text_lines = [result[1] for result in results]
        return '\n'.join(text_lines)

    @staticmethod
    def _generate_summary(text: str) -> str:
        """
        Generate a summary from extracted text.
        
        Args:
            text: Extracted text content.
            
        Returns:
            Summary of the text.
        """
        if not text:
            return "No text content found in the document."
        
        # Clean up the text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if len(lines) == 0:
            return "No readable text found in the document."
        
        # Take first meaningful lines as summary
        summary_lines = lines[:20]
        summary = '\n'.join(summary_lines)
        
        # Truncate if too long
        if len(summary) > 1000:
            summary = summary[:1000] + "..."
        
        # Add word count info
        word_count = len(text.split())
        char_count = len(text)
        
        summary += f"\n\n--- Document Statistics ---"
        summary += f"\nWords: {word_count}"
        summary += f"\nCharacters: {char_count}"
        summary += f"\nLines: {len(lines)}"
        
        return summary

    @staticmethod
    async def summarize_image(image_bytes: bytes) -> str:
        """
        Extract and summarize text from an image.
        
        Args:
            image_bytes: Raw bytes of the image file.
            
        Returns:
            Summary of the image content.
        """
        if not OCRService._initialized:
            OCRService.initialize_model()
        
        text = await OCRService._extract_text(image_bytes)
        return OCRService._generate_summary(text)

    @staticmethod
    async def summarize_pdf(pdf_bytes: bytes) -> Tuple[str, int]:
        """
        Extract and summarize text from a PDF document.
        
        Args:
            pdf_bytes: Raw bytes of the PDF file.
            
        Returns:
            Tuple of (summary, total_pages).
        """
        if not OCRService._initialized:
            OCRService.initialize_model()
        
        # Open PDF
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(pdf_document)
        
        all_text = []
        
        # Process up to first 5 pages
        pages_to_process = min(total_pages, 5)
        
        for page_num in range(pages_to_process):
            page = pdf_document[page_num]
            
            # Try to extract text directly from PDF first
            page_text = page.get_text()
            
            # If no text found, use OCR on the page image
            if not page_text.strip():
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                page_img = pix.tobytes("png")
                page_text = await OCRService._extract_text(page_img)
            
            if page_text.strip():
                all_text.append(f"--- Page {page_num + 1} ---\n{page_text.strip()}")
        
        pdf_document.close()
        
        # Combine all text
        combined_text = '\n\n'.join(all_text)
        
        # Generate summary
        summary = OCRService._generate_summary(combined_text)
        
        # Add page info
        if total_pages > pages_to_process:
            summary += f"\n\n[Note: Document has {total_pages} pages. Processed first {pages_to_process} pages.]"
        else:
            summary += f"\n\n[Processed all {total_pages} page(s).]"
        
        return summary, total_pages
