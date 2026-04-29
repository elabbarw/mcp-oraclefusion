"""
Oracle Fusion MCP Server — STDIO transport

Thin wrapper for backward compatibility with `python stdio_server.py`.
The actual implementation lives in oracle_fusion_mcp.cli.
"""

from oracle_fusion_mcp.cli import main

if __name__ == "__main__":
    main()
