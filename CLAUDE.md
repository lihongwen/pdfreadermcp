# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Server
```bash
uv run pdfreadermcp
```

### Package Management
```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --dev

# Run tests using test files (no pytest configuration yet)
uv run python test_easyocr.py
```

### Project Setup
- Uses `uv` package manager for Python dependency management
- Python 3.11+ required (see .python-version)
- Entry point: `src/pdfreadermcp/__main__.py`
- Uses Chinese PyPI mirrors for faster dependency installation

## Architecture Overview

### MCP Server Structure
This is an MCP (Model Context Protocol) server built with FastMCP that provides PDF processing capabilities.

**Core Components:**
- `src/pdfreadermcp/server.py`: FastMCP server with tool definitions (`read_pdf`, `ocr_pdf`)
- `src/pdfreadermcp/tools/pdf_reader.py`: Text extraction using pdfplumber
- `src/pdfreadermcp/tools/pdf_ocr.py`: OCR processing using **EasyOCR** (not PaddleOCR)
- `src/pdfreadermcp/utils/`: Supporting utilities for caching, chunking, and file handling

### Tool Architecture
- **read_pdf**: Intelligent text extraction with quality detection
- **ocr_pdf**: EasyOCR-based OCR for scanned documents
- Both tools support flexible page range syntax: `"1,3,5-10,-1"`
- Output format: Structured JSON with chunks, metadata, and quality scores

### Key Features
- **Smart caching system**: File-based invalidation in `utils/cache.py`
- **Text quality analysis**: Automatic detection of when OCR is needed
- **Chunking strategies**: Configurable text splitting with overlap preservation
- **Multi-language OCR**: EasyOCR with Chinese and English support by default

### Dependencies (IMPORTANT: EasyOCR, not PaddleOCR)
- **Core**: mcp[cli], pdfplumber, pdf2image, easyocr, torch, numpy
- **Text processing**: langchain-text-splitters for chunking
- **Image processing**: pillow for image handling
- **Configuration**: Uses Chinese PyPI mirrors for faster installation

### OCR Engine Details
The server uses **EasyOCR**, not PaddleOCR as incorrectly stated in the original CLAUDE.md:
- Default languages: `ch_sim,en` (Simplified Chinese, English)
- GPU support available via `use_gpu` parameter
- First run downloads OCR models automatically

### Configuration
- Uses FastMCP framework for MCP server implementation
- Tools are async functions decorated with `@app.tool()`
- Error handling returns structured JSON responses
- Chinese index URLs (Tsinghua mirrors) configured in pyproject.toml

## Testing
- Test files: `test_easyocr.py`, `test_ocr.py`, `simple_ocr_test.py` in root directory
- Tests are standalone scripts, not using pytest framework
- Run individual test files: `uv run python test_easyocr.py`