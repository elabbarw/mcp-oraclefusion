"""HCM user account tool definitions and handlers."""

from typing import Any, Dict
from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...oracle.client import OracleClient
from ._helpers import _text_result

TOOLS = [
    {"name": "search_user_accounts", "description": "Search HCM user accounts in Oracle Fusion by username or email.", "inputSchema": {"type": "object", "properties": {"username": {"type": "string", "description": "Username or partial email, partial match supported."}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
]

async def handle_search_user_accounts(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_user_accounts(username=params.get("username"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

HANDLERS = {"search_user_accounts": handle_search_user_accounts}
