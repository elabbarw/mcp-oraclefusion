"""General Ledger tool definitions and handlers."""

from typing import Any, Dict
from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...oracle.client import OracleClient
from ._helpers import _text_result

TOOLS = [
    {"name": "search_journal_batches", "description": "Search General Ledger journal batches in Oracle Fusion.", "inputSchema": {"type": "object", "properties": {"period": {"type": "string", "description": "Format: 'Mon-YY'"}, "status": {"type": "string"}, "source": {"type": "string"}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
    {"name": "search_gl_balances", "description": "Get GL account balances. ALL parameters are REQUIRED by the Oracle API.", "inputSchema": {"type": "object", "properties": {"ledger": {"type": "string", "description": "Ledger name, exact match. REQUIRED."}, "account_combination": {"type": "string", "description": "Chart of accounts combination. REQUIRED."}, "period": {"type": "string", "description": "Accounting period. REQUIRED. Format: 'Mon-YY'"}, "currency": {"type": "string", "description": "Currency code. REQUIRED."}, "mode": {"type": "string", "default": "Detail"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": ["ledger", "account_combination", "period", "currency"]}},
    {"name": "list_ledgers", "description": "List defined ledgers in Oracle Fusion General Ledger.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "ledger_type": {"type": "string", "enum": ["Primary", "Secondary", "ALC"]}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
    {"name": "list_chart_of_accounts", "description": "List chart of accounts structures defined in Oracle Fusion.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
    {"name": "search_currency_rates", "description": "Search daily currency exchange rates in Oracle Fusion.", "inputSchema": {"type": "object", "properties": {"from_currency": {"type": "string"}, "to_currency": {"type": "string"}, "conversion_type": {"type": "string", "default": "Corporate"}, "start_date": {"type": "string"}, "end_date": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
]

async def handle_search_journal_batches(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_journal_batches(period=params.get("period"), status=params.get("status"), source=params.get("source"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_search_gl_balances(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_gl_balances(ledger=params.get("ledger", ""), account_combination=params.get("account_combination", ""), period=params.get("period", ""), currency=params.get("currency", ""), mode=params.get("mode", "Detail"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_list_ledgers(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.list_ledgers(name=params.get("name"), ledger_type=params.get("ledger_type"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_list_chart_of_accounts(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.list_chart_of_accounts(name=params.get("name"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_search_currency_rates(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_currency_rates(from_currency=params.get("from_currency", ""), to_currency=params.get("to_currency", ""), conversion_type=params.get("conversion_type", "Corporate"), start_date=params.get("start_date"), end_date=params.get("end_date"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

HANDLERS = {"search_journal_batches": handle_search_journal_batches, "search_gl_balances": handle_search_gl_balances, "list_ledgers": handle_list_ledgers, "list_chart_of_accounts": handle_list_chart_of_accounts, "search_currency_rates": handle_search_currency_rates}
