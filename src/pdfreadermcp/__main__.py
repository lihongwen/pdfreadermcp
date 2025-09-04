"""
Entry point for the PDF Reader MCP server using FastMCP.
"""

from .server import app

def main():
    """Main entry point for the MCP server."""
    app.run()

if __name__ == "__main__":
    main()