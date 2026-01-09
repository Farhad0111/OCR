# Service logic for OCR processing using EasyOCR (CPU-friendly)

import os
import re
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from typing import Tuple
import numpy as np

# Load environment variables
load_dotenv()

# Summary configuration
MAX_SUMMARY_SENTENCES = int(os.getenv("MAX_SUMMARY_SENTENCES", "5"))


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
        """
        if OCRService._reader is None:
            OCRService.initialize_model()
        
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)
        
        results = OCRService._reader.readtext(image_np)
        text_lines = [result[1] for result in results]
        return ' '.join(text_lines)

    @staticmethod
    def _extract_sentences(text: str) -> list:
        """Extract sentences from text."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return sentences

    @staticmethod
    def _generate_summary(text: str, num_sentences: int = None) -> str:
        """
        Generate a summary with specified number of sentences.
        """
        if not text:
            return "No text content found in the document."
        
        if num_sentences is None:
            num_sentences = MAX_SUMMARY_SENTENCES
        
        sentences = OCRService._extract_sentences(text)
        
        if len(sentences) == 0:
            return text[:500] + "..." if len(text) > 500 else text
        
        summary_sentences = sentences[:num_sentences]
        summary = ' '.join(summary_sentences)
        
        word_count = len(text.split())
        char_count = len(text)
        total_sentences = len(sentences)
        
        summary += f"\n\n--- Statistics ---"
        summary += f"\nSummary: {len(summary_sentences)} of {total_sentences} sentences"
        summary += f"\nTotal Words: {word_count}"
        summary += f"\nTotal Characters: {char_count}"
        
        return summary

    @staticmethod
    async def summarize_image(image_bytes: bytes) -> str:
        """Extract and summarize text from an image."""
        if not OCRService._initialized:
            OCRService.initialize_model()
        
        text = await OCRService._extract_text(image_bytes)
        return OCRService._generate_summary(text)

    @staticmethod
    async def summarize_pdf(pdf_bytes: bytes) -> Tuple[str, int]:
        """Extract and summarize text from a PDF document."""
        if not OCRService._initialized:
            OCRService.initialize_model()
        
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(pdf_document)
        
        all_text = []
        pages_to_process = min(total_pages, 10)
        
        for page_num in range(pages_to_process):
            page = pdf_document[page_num]
            page_text = page.get_text()
            
            if not page_text.strip():
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                page_img = pix.tobytes("png")
                page_text = await OCRService._extract_text(page_img)
            
            if page_text.strip():
                all_text.append(page_text.strip())
        
        pdf_document.close()
        
        combined_text = ' '.join(all_text)
        summary = OCRService._generate_summary(combined_text)
        
        if total_pages > pages_to_process:
            summary += f"\n\n[Note: Document has {total_pages} pages. Processed first {pages_to_process} pages.]"
        
        return summary, total_pages

    @staticmethod
    async def summarize_txt(txt_bytes: bytes) -> str:
        """Extract and summarize text from a text file."""
        text = None
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                text = txt_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if text is None:
            raise ValueError("Unable to decode text file. Unsupported encoding.")
        
        text = text.strip()
        
        if not text:
            return "The text file is empty."
        
        return OCRService._generate_summary(text)

    @staticmethod
    async def summarize_docx(docx_bytes: bytes) -> Tuple[str, int]:
        """Extract and summarize text from a DOCX document."""
        try:
            from docx import Document
        except ImportError:
            raise RuntimeError("python-docx not installed. Run: pip install python-docx")
        
        doc = Document(BytesIO(docx_bytes))
        
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        
        total_paragraphs = len(paragraphs)
        
        if total_paragraphs == 0:
            return "The document is empty or contains no readable text.", 0
        
        combined_text = ' '.join(paragraphs)
        summary = OCRService._generate_summary(combined_text)
        
        return summary, total_paragraphs
