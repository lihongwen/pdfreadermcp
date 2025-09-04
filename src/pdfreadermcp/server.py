"""
MCP Server for PDF reading with text extraction and OCR support using FastMCP.
"""

from typing import Any
from mcp.server.fastmcp import FastMCP
from .tools.pdf_reader import PDFReader
from .tools.pdf_ocr import PDFOCR

# Create FastMCP app
app = FastMCP("PDF Reader MCP Server")

# Initialize PDF processing tools
pdf_reader = PDFReader()
pdf_ocr = PDFOCR()


@app.tool()
async def read_pdf(
    file_path: str,
    pages: str = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 100
) -> str:
    """Extract text from PDF files with intelligent page handling and chunking.
    
    Args:
        file_path: Path to the PDF file
        pages: Page range (e.g., '1,3,5-10,-1' for pages 1, 3, 5 to 10, and last page)
        chunk_size: Maximum size of text chunks
        chunk_overlap: Overlap between chunks to preserve context
        
    Returns:
        JSON string with extracted text and metadata
    """
    try:
        result = await pdf_reader.extract_text(
            file_path=file_path,
            pages=pages,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return result
    except Exception as e:
        import json
        return json.dumps({
            'success': False,
            'error': f'PDF text extraction failed: {str(e)}',
            'extraction_method': 'text_extraction'
        }, ensure_ascii=False, indent=2)


@app.tool()
async def ocr_pdf(
    file_path: str,
    pages: str = None,
    language: str = "ch_sim,en",
    chunk_size: int = 1000
) -> str:
    """Perform OCR on PDF pages using PaddleOCR for scanned documents.
    
    Args:
        file_path: Path to the PDF file
        pages: Page range (e.g., '1,3,5-10,-1' for pages 1, 3, 5 to 10, and last page)
        language: OCR language codes (e.g., 'ch_sim,en' for Chinese and English)
        chunk_size: Maximum size of text chunks
        
    Returns:
        JSON string with OCR results and metadata
    """
    try:
        result = await pdf_ocr.extract_text_ocr(
            file_path=file_path,
            pages=pages,
            language=language,
            chunk_size=chunk_size
        )
        return result
    except Exception as e:
        import json
        return json.dumps({
            'success': False,
            'error': f'PDF OCR extraction failed: {str(e)}',
            'extraction_method': 'paddleocr'
        }, ensure_ascii=False, indent=2)