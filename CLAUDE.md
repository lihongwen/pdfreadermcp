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

# Install with dev dependencies (when available)
uv sync --dev

# Run tests (when available)
uv run pytest
```

### Project Setup
- Uses `uv` package manager for Python dependency management
- Python 3.11+ required
- Entry point: `src/pdfreadermcp/__main__.py`

## Architecture Overview

### MCP Server Structure
This is an MCP (Model Context Protocol) server built with FastMCP that provides PDF processing capabilities.

**Core Components:**
- `server.py`: FastMCP server with tool definitions (`read_pdf`, `ocr_pdf`)
- `tools/pdf_reader.py`: Text extraction using pdfplumber
- `tools/pdf_ocr.py`: OCR processing using PaddleOCR
- `utils/`: Supporting utilities for caching, chunking, and file handling

### Tool Architecture
- **read_pdf**: Intelligent text extraction with quality detection
- **ocr_pdf**: PaddleOCR-based OCR for scanned documents
- Both tools support flexible page range syntax: `"1,3,5-10,-1"`
- Output format: Structured JSON with chunks, metadata, and quality scores

### Key Features
- **Smart caching system**: File-based invalidation in `utils/cache.py`
- **Text quality analysis**: Automatic detection of when OCR is needed
- **Chunking strategies**: Configurable text splitting with overlap preservation
- **Multi-language OCR**: PaddleOCR with 80+ language support

### Dependencies
- **Core**: mcp[cli], pdfplumber, pdf2image, paddlepaddle, paddleocr
- **Text processing**: langchain-text-splitters for chunking
- **Image processing**: pillow for image handling
- **Special index configuration**: Uses Chinese mirrors for PaddlePaddle

### Configuration
- Uses FastMCP framework for MCP server implementation
- Tools are async functions decorated with `@app.tool()`
- Error handling returns structured JSON responses
- Chinese index URLs configured for PaddlePaddle dependencies