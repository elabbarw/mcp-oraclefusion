"""Expense report tool definitions and handlers."""

from typing import Any, Dict
from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...oracle.client import OracleClient
from ._helpers import _text_result

TOOLS = [
    {"name": "search_expense_reports", "description": "Search employee expense reports in Oracle Fusion. NOTE: May return 403 depending on service account privileges.", "inputSchema": {"type": "object", "properties": {"employee": {"type": "string"}, "status": {"type": "string"}, "business_unit": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
]

async def handle_search_expense_reports(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_expense_reports(employee=params.get("employee"), status=params.get("status"), business_unit=params.get("business_unit"), date_from=params.get("date_from"), date_to=params.get("date_to"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

HANDLERS = {"search_expense_reports": handle_search_expense_reports}
