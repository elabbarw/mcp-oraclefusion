"""AP Invoice and Payment tool definitions and handlers."""

from typing import Any, Dict
from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...oracle.client import OracleClient
from ._helpers import _text_result

TOOLS = [
    {"name": "search_invoices", "description": "Search Accounts Payable invoices in Oracle Fusion. Examples: search_invoices({\"supplier\": \"google\"}) finds invoices from Google. search_invoices({\"invoice_number\": \"INV-001\"}) finds a specific invoice. search_invoices({\"date_from\": \"2024-01-01\", \"date_to\": \"2024-03-31\"}) finds invoices in Q1 2024.", "inputSchema": {"type": "object", "properties": {"supplier": {"type": "string", "description": "Supplier/vendor name to search for. Partial match from start, automatically uppercased."}, "invoice_number": {"type": "string", "description": "Exact invoice number."}, "business_unit": {"type": "string", "description": "Business unit name, exact match."}, "status": {"type": "string", "description": "Invoice validation status. Values: 'Validated', 'Needs Revalidation', 'Unvalidated'"}, "date_from": {"type": "string", "description": "Start of invoice date range. Format: YYYY-MM-DD"}, "date_to": {"type": "string", "description": "End of invoice date range. Format: YYYY-MM-DD"}, "q": {"type": "string", "description": "Advanced Oracle REST filter. Use Oracle syntax with semicolons as AND."}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
    {"name": "get_invoice_details", "description": "Get full details for a single AP invoice by its numeric InvoiceId.", "inputSchema": {"type": "object", "properties": {"invoice_id": {"type": "integer"}, "expand_lines": {"type": "boolean", "default": False}}, "required": ["invoice_id"]}},
    {"name": "search_payments", "description": "Search Accounts Payable payments in Oracle Fusion.", "inputSchema": {"type": "object", "properties": {"supplier": {"type": "string"}, "status": {"type": "string"}, "business_unit": {"type": "string"}, "date_from": {"type": "string"}, "date_to": {"type": "string"}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
    {"name": "get_payment_details", "description": "Get full details for a single AP payment by its numeric PaymentId.", "inputSchema": {"type": "object", "properties": {"payment_id": {"type": "integer"}}, "required": ["payment_id"]}},
    {"name": "list_payment_terms", "description": "List Accounts Payable payment terms defined in Oracle Fusion.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
]

async def handle_search_invoices(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_invoices(business_unit=params.get("business_unit"), supplier=params.get("supplier"), invoice_number=params.get("invoice_number"), date_from=params.get("date_from"), date_to=params.get("date_to"), status=params.get("status"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_get_invoice_details(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.get_invoice(invoice_id=params["invoice_id"], expand_lines=params.get("expand_lines", False)))

async def handle_search_payments(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_payments(supplier=params.get("supplier"), status=params.get("status"), business_unit=params.get("business_unit"), date_from=params.get("date_from"), date_to=params.get("date_to"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_get_payment_details(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.get_payment_details(payment_id=params["payment_id"]))

async def handle_list_payment_terms(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.list_payment_terms(name=params.get("name"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

HANDLERS = {"search_invoices": handle_search_invoices, "get_invoice_details": handle_get_invoice_details, "search_payments": handle_search_payments, "get_payment_details": handle_get_payment_details, "list_payment_terms": handle_list_payment_terms}
