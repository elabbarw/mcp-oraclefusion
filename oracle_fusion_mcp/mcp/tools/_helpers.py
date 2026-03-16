"""Shared helpers for MCP tool modules."""

import json
from typing import Any, Dict


def _text_result(data: Any) -> Dict[str, Any]:
    """Wrap a Python object as MCP text content."""
    return {
        "content": [{
            "type": "text",
            "text": json.dumps(data, indent=2, default=str)
        }]
    }
