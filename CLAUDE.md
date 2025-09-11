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

# Run tests (if any test files exist)
```

### Project Setup
- Uses `uv` package manager for Python dependency management
- Python 3.11+ required (see .python-version)
- Entry point: `src/pdfreadermcp/__main__.py`
- Uses Chinese PyPI mirrors for faster dependency installation

## Architecture Overview

### MCP Server Structure
This is an MCP (Model Context Protocol) server built with FastMCP that provides PDF text extraction and document operation capabilities.

**Core Components:**
- `src/pdfreadermcp/server.py`: FastMCP server with tool definitions (`read_pdf`, `split_pdf`, `extract_pages`, `merge_pdfs`)
- `src/pdfreadermcp/tools/pdf_reader.py`: Text extraction using pdfplumber
- `src/pdfreadermcp/tools/pdf_operations.py`: PDF document operations using pypdf
- `src/pdfreadermcp/utils/`: Supporting utilities for caching, chunking, and file handling

### Tool Architecture
- **read_pdf**: Intelligent text extraction with quality detection
- **split_pdf**: Split PDF into multiple files by page ranges
- **extract_pages**: Extract specific pages to a new PDF file
- **merge_pdfs**: Merge multiple PDF files into one
- All tools support flexible page range syntax: `"1,3,5-10,-1"`
- Output format: Structured JSON with results, metadata, and file information

### Key Features
- **Smart caching system**: File-based invalidation in `utils/cache.py`
- **Text quality analysis**: Automatic detection of text content quality
- **Chunking strategies**: Configurable text splitting with overlap preservation
- **PDF document operations**: Split, extract, and merge PDF files
- **Flexible output control**: Custom output directories and filenames
- **Default behavior**: Operations save to source file directory by default

### Dependencies
- **Core**: mcp[cli], pdfplumber, pypdf
- **Text processing**: langchain-text-splitters for chunking  
- **Document operations**: pypdf for PDF manipulation
- **Configuration**: Uses Chinese PyPI mirrors for faster installation

### Configuration
- Uses FastMCP framework for MCP server implementation
- Tools are async functions decorated with `@app.tool()`
- Error handling returns structured JSON responses
- Chinese index URLs (Tsinghua mirrors) configured in pyproject.toml

## Available Tools

### Text Extraction
- `read_pdf`: Extract and chunk text from PDF files with quality analysis

### PDF Operations
- `split_pdf`: Split PDF into multiple files by page ranges
- `extract_pages`: Extract specific pages to a new PDF file  
- `merge_pdfs`: Merge multiple PDF files into one document

### Usage Examples
```python
# Split a PDF into multiple files
split_pdf(file_path="document.pdf", split_ranges=["1-10", "11-20", "21-30"])

# Extract specific pages
extract_pages(file_path="document.pdf", pages="1,3,5-7", output_file="selected_pages.pdf")

# Merge PDFs
merge_pdfs(file_paths=["doc1.pdf", "doc2.pdf", "doc3.pdf"], output_file="combined.pdf")
```

## Output File Conventions
- **Split files**: `{original_name}_split_{number}.pdf`
- **Extracted pages**: `{original_name}_pages_{page_range}.pdf`
- **Merged files**: `merged_{timestamp}.pdf` (if no output filename specified)
- **Default location**: Same directory as source file(s)

## Testing
- Currently no test files available
- Tests would be standalone scripts, not using pytest framework