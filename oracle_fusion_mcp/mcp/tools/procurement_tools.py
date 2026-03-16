"""Procurement tool definitions and handlers (POs, suppliers, requisitions, receipts, ASL, categories)."""

from typing import Any, Dict
from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...oracle.client import OracleClient
from ._helpers import _text_result

TOOLS = [
    {"name": "search_purchase_orders", "description": "Search purchase orders in Oracle Fusion Procurement.", "inputSchema": {"type": "object", "properties": {"supplier": {"type": "string"}, "status": {"type": "string", "description": "Values: 'OPEN', 'CLOSED', 'APPROVED', 'INCOMPLETE'"}, "buyer": {"type": "string"}, "requester": {"type": "string", "description": "Partial match on RequesterDisplayName. Note: filtered client-side."}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
    {"name": "get_po_details", "description": "Get full details for a single purchase order by its numeric POHeaderId, including lines.", "inputSchema": {"type": "object", "properties": {"po_id": {"type": "integer"}}, "required": ["po_id"]}},
    {"name": "search_suppliers", "description": "Search supplier master data in Oracle Fusion. Note: Status is not filterable via the Oracle REST API.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "supplier_type": {"type": "string"}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
    {"name": "get_supplier_details", "description": "Get full details for a single supplier by its numeric SupplierId, including sites, contacts, and addresses.", "inputSchema": {"type": "object", "properties": {"supplier_id": {"type": "integer"}}, "required": ["supplier_id"]}},
    {"name": "search_requisitions", "description": "Search purchase requisitions in Oracle Fusion.", "inputSchema": {"type": "object", "properties": {"preparer": {"type": "string"}, "status": {"type": "string"}, "business_unit": {"type": "string"}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
    {"name": "search_receiving_receipts", "description": "Look up a goods receiving receipt by its receipt number. Receipt number is REQUIRED by the Oracle API.", "inputSchema": {"type": "object", "properties": {"receipt_number": {"type": "string", "description": "REQUIRED."}}, "required": ["receipt_number"]}},
    {"name": "search_approved_suppliers", "description": "Search the approved supplier list in Oracle Fusion Procurement.", "inputSchema": {"type": "object", "properties": {"supplier": {"type": "string"}, "item": {"type": "string"}, "status": {"type": "string"}, "procurement_bu": {"type": "string"}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
    {"name": "search_categories", "description": "Search procurement browsing categories in Oracle Fusion.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "category_type": {"type": "string"}, "q": {"type": "string"}, "limit": {"type": "integer", "default": 25}, "offset": {"type": "integer", "default": 0}}, "required": []}},
]

async def handle_search_purchase_orders(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_purchase_orders(supplier=params.get("supplier"), status=params.get("status"), buyer=params.get("buyer"), requester=params.get("requester"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_get_po_details(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.get_purchase_order(po_id=params["po_id"]))

async def handle_search_suppliers(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_suppliers(name=params.get("name"), supplier_type=params.get("supplier_type"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_get_supplier_details(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    return _text_result(await oracle_client.get_supplier_details(supplier_id=params["supplier_id"]))

async def handle_search_requisitions(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_requisitions(preparer=params.get("preparer"), status=params.get("status"), business_unit=params.get("business_unit"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_search_receiving_receipts(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    receipt_number = params.get("receipt_number", "")
    if not receipt_number:
        return _text_result({"error": "receipt_number is required by the Oracle API"})
    records, has_more, total = await oracle_client.search_receiving_receipts(receipt_number=receipt_number, limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_search_approved_suppliers(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_approved_suppliers(supplier=params.get("supplier"), item=params.get("item"), status=params.get("status"), procurement_bu=params.get("procurement_bu"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

async def handle_search_categories(request: Request, session: ValidatedUser, params: Dict[str, Any], oracle_client: OracleClient) -> Dict[str, Any]:
    records, has_more, total = await oracle_client.search_categories(name=params.get("name"), category_type=params.get("category_type"), q=params.get("q"), limit=params.get("limit", 25), offset=params.get("offset", 0))
    return _text_result({"records": records, "has_more": has_more, "total": total})

HANDLERS = {"search_purchase_orders": handle_search_purchase_orders, "get_po_details": handle_get_po_details, "search_suppliers": handle_search_suppliers, "get_supplier_details": handle_get_supplier_details, "search_requisitions": handle_search_requisitions, "search_receiving_receipts": handle_search_receiving_receipts, "search_approved_suppliers": handle_search_approved_suppliers, "search_categories": handle_search_categories}
