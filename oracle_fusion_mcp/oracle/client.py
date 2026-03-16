"""Oracle Fusion REST API client"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx

from ..config.settings import get_settings
from .field_maps import (
    INVOICE_FIELD_MAP, PO_FIELD_MAP, SUPPLIER_FIELD_MAP,
    INVOICE_DEFAULT_FIELDS, PO_DEFAULT_FIELDS, SUPPLIER_DEFAULT_FIELDS,
    PAYMENT_FIELD_MAP, PAYMENT_DEFAULT_FIELDS,
    JOURNAL_BATCH_FIELD_MAP, JOURNAL_BATCH_DEFAULT_FIELDS,
    GL_BALANCE_FIELD_MAP, GL_BALANCE_DEFAULT_FIELDS,
    LEDGER_FIELD_MAP, LEDGER_DEFAULT_FIELDS,
    CHART_OF_ACCOUNTS_FIELD_MAP, CHART_OF_ACCOUNTS_DEFAULT_FIELDS,
    CURRENCY_RATE_FIELD_MAP,
    PAYMENT_TERMS_FIELD_MAP, PAYMENT_TERMS_DEFAULT_FIELDS,
    APPROVED_SUPPLIER_FIELD_MAP, APPROVED_SUPPLIER_DEFAULT_FIELDS,
    BROWSING_CATEGORY_FIELD_MAP, BROWSING_CATEGORY_DEFAULT_FIELDS,
    AR_INVOICE_FIELD_MAP, AR_INVOICE_DEFAULT_FIELDS,
    RECEIPT_FIELD_MAP, RECEIPT_DEFAULT_FIELDS,
    REQUISITION_FIELD_MAP, REQUISITION_DEFAULT_FIELDS,
    RECEIVING_RECEIPT_FIELD_MAP, RECEIVING_RECEIPT_DEFAULT_FIELDS,
    EXPENSE_REPORT_FIELD_MAP, EXPENSE_REPORT_DEFAULT_FIELDS,
    USER_ACCOUNT_FIELD_MAP, USER_ACCOUNT_DEFAULT_FIELDS,
)

logger = logging.getLogger(__name__)


class OracleClient:
    """Async HTTP client for Oracle Fusion REST API"""

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        bearer_token: Optional[str] = None,
    ):
        self.settings = get_settings()
        self._username = username
        self._password = password
        self._bearer_token = bearer_token

    def _get_auth(self) -> Optional[httpx.BasicAuth]:
        if self._bearer_token:
            return None
        if self._username and self._password:
            return httpx.BasicAuth(self._username, self._password)
        return None

    def _get_headers(self) -> Dict[str, str]:
        if self._bearer_token:
            return {"Authorization": f"Bearer {self._bearer_token}"}
        return {}

    def _build_params(
        self,
        fields: Optional[List[str]] = None,
        q: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
        expand: Optional[str] = None,
        total_results: bool = False,
    ) -> Dict[str, str]:
        params: Dict[str, str] = {
            "limit": str(limit),
            "offset": str(offset),
            "onlyData": "true",
        }
        if fields:
            params["fields"] = ",".join(fields)
        if q:
            params["q"] = q
        if expand:
            params["expand"] = expand
        if total_results:
            params["totalResults"] = "true"
        return params

    async def _fetch(
        self, endpoint: str, params: Dict[str, str]
    ) -> Dict[str, Any]:
        url = f"{self.settings.oracle_api_base}/{endpoint}"
        auth = self._get_auth()
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(url, params=params, auth=auth, headers=headers)
            if resp.status_code == 500:
                # Retry 1: drop totalResults (expensive COUNT on large tables)
                if params.pop("totalResults", None):
                    logger.warning("Oracle 500 on %s with totalResults — retrying without", endpoint)
                    resp = await client.get(url, params=params, auth=auth, headers=headers)
            if resp.status_code == 500:
                # Retry 2: drop fields projection (some fields cause 500 in collection queries)
                if params.pop("fields", None):
                    logger.warning("Oracle 500 on %s with fields projection — retrying without", endpoint)
                    resp = await client.get(url, params=params, auth=auth, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def _post(
        self, endpoint: str, body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """POST to Oracle REST API. No retry logic — writes must not auto-retry."""
        url = f"{self.settings.oracle_api_base}/{endpoint}"
        auth = self._get_auth()
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=body, auth=auth, headers=headers)
            if not resp.is_success:
                self._raise_oracle_error(resp, endpoint)
            return resp.json()

    async def _patch(
        self, endpoint: str, body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """PATCH to Oracle REST API. No retry logic — writes must not auto-retry."""
        url = f"{self.settings.oracle_api_base}/{endpoint}"
        auth = self._get_auth()
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.patch(url, json=body, auth=auth, headers=headers)
            if not resp.is_success:
                self._raise_oracle_error(resp, endpoint)
            return resp.json()

    def _raise_oracle_error(self, resp: httpx.Response, endpoint: str) -> None:
        """Extract Oracle's error detail from a failed response and raise."""
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        logger.error("Oracle %s on %s: %s", resp.status_code, endpoint, detail)
        raise httpx.HTTPStatusError(
            f"Oracle {resp.status_code}: {detail}",
            request=resp.request,
            response=resp,
        )

    async def _post_action(
        self, endpoint: str, body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """POST to an Oracle REST action endpoint."""
        url = f"{self.settings.oracle_api_base}/{endpoint}"
        auth = self._get_auth()
        headers = self._get_headers()
        headers["Content-Type"] = "application/vnd.oracle.adf.action+json"
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=body or {}, auth=auth, headers=headers)
            if not resp.is_success:
                self._raise_oracle_error(resp, endpoint)
            return resp.json() if resp.text.strip() else {"status": "success"}

    async def _fetch_hcm(
        self, endpoint: str, params: Dict[str, str]
    ) -> Dict[str, Any]:
        url = f"{self.settings.oracle_hcm_base}/{endpoint}"
        auth = self._get_auth()
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params=params, auth=auth, headers=headers)
            if resp.status_code == 500:
                if params.pop("totalResults", None):
                    logger.warning("Oracle 500 on HCM %s with totalResults — retrying without", endpoint)
                    resp = await client.get(url, params=params, auth=auth, headers=headers)
            if resp.status_code == 500:
                if params.pop("fields", None):
                    logger.warning("Oracle 500 on HCM %s with fields projection — retrying without", endpoint)
                    resp = await client.get(url, params=params, auth=auth, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def test_connection(self) -> Dict[str, Any]:
        """Test Oracle API connection, return record counts"""
        start = time.time()
        try:
            inv = await self._fetch("invoices", {"limit": "1", "totalResults": "true", "onlyData": "true", "fields": "InvoiceId"})
            po = await self._fetch("purchaseOrders", {"limit": "1", "totalResults": "true", "onlyData": "true", "fields": "POHeaderId"})
            sup = await self._fetch("suppliers", {"limit": "1", "totalResults": "true", "onlyData": "true", "fields": "SupplierId"})
            latency = (time.time() - start) * 1000
            return {
                "success": True,
                "invoice_count": inv.get("totalResults"),
                "po_count": po.get("totalResults"),
                "supplier_count": sup.get("totalResults"),
                "latency_ms": round(latency, 1),
            }
        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search_invoices(self, q=None, business_unit=None, supplier=None, invoice_number=None, date_from=None, date_to=None, status=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if business_unit: conditions.append(f"BusinessUnit = '{business_unit}'")
        if supplier: conditions.append(f"Supplier LIKE '{supplier.upper()}*'")
        if invoice_number: conditions.append(f"InvoiceNumber = '{invoice_number}'")
        if date_from: conditions.append(f"InvoiceDate >= '{date_from}'")
        if date_to: conditions.append(f"InvoiceDate <= '{date_to}'")
        if status: conditions.append(f"ValidationStatus = '{status}'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=INVOICE_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("invoices", params)
        records = self._map_fields(data.get("items", []), INVOICE_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def get_invoice(self, invoice_id: int, expand_lines: bool = True) -> Optional[Dict]:
        params = self._build_params(limit=1)
        if expand_lines:
            params["expand"] = "invoiceLines"
        params["finder"] = f"PrimaryKey;InvoiceId={invoice_id}"
        data = await self._fetch("invoices", params)
        items = data.get("items", [])
        return items[0] if items else None

    async def search_purchase_orders(self, q=None, supplier=None, status=None, buyer=None, requester=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if supplier: conditions.append(f"Supplier LIKE '{supplier.upper()}*'")
        if status: conditions.append(f"Status = '{status}'")
        if buyer: conditions.append(f"Buyer LIKE '*{buyer}*'")
        if requester:
            return await self._search_pos_by_requester(requester, conditions, limit, offset)
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=PO_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("purchaseOrders", params)
        records = self._map_fields(data.get("items", []), PO_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def _search_pos_by_requester(self, requester, base_conditions, limit, offset):
        requester_upper = requester.upper()
        matched = []
        batch_size = 500
        current_offset = 0
        needed = offset + limit
        while True:
            query = ";".join(base_conditions) if base_conditions else None
            params = self._build_params(fields=PO_DEFAULT_FIELDS, q=query, limit=batch_size, offset=current_offset, total_results=True)
            data = await self._fetch("purchaseOrders", params)
            for po in data.get("items", []):
                if requester_upper in (po.get("RequesterDisplayName") or "").upper():
                    matched.append(po)
            if not data.get("hasMore", False) or len(matched) >= needed:
                break
            current_offset += batch_size
        result_slice = matched[offset:offset + limit]
        return self._map_fields(result_slice, PO_FIELD_MAP), len(matched) > offset + limit, len(matched)

    async def get_purchase_order(self, po_id: int) -> Optional[Dict]:
        params = self._build_params(limit=1)
        params["expand"] = "lines"
        params["q"] = f"POHeaderId = {po_id}"
        data = await self._fetch("purchaseOrders", params)
        items = data.get("items", [])
        return items[0] if items else None

    async def search_suppliers(self, name=None, q=None, supplier_type=None, limit=25, offset=0):
        conditions = []
        if name: conditions.append(f"Supplier LIKE '*{name.upper()}*'")
        if q: conditions.append(q)
        if supplier_type: conditions.append(f"SupplierType = '{supplier_type}'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=SUPPLIER_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("suppliers", params)
        records = self._map_fields(data.get("items", []), SUPPLIER_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def search_user_accounts(self, username=None, limit=25, offset=0):
        conditions = [f"Username LIKE '*{username}*'"] if username else []
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=USER_ACCOUNT_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        params["expand"] = "userAccountRoles"
        data = await self._fetch_hcm("userAccounts", params)
        records = self._map_fields(data.get("items", []), USER_ACCOUNT_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def search_payments(self, supplier=None, status=None, business_unit=None, date_from=None, date_to=None, q=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if supplier: conditions.append(f"Payee LIKE '*{supplier}*'")
        if status: conditions.append(f"PaymentStatus = '{status}'")
        if business_unit: conditions.append(f"BusinessUnit = '{business_unit}'")
        if date_from: conditions.append(f"PaymentDate >= '{date_from}'")
        if date_to: conditions.append(f"PaymentDate <= '{date_to}'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=PAYMENT_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("payablesPayments", params)
        records = self._map_fields(data.get("items", []), PAYMENT_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def get_payment_details(self, payment_id: int) -> Optional[Dict]:
        params = self._build_params(limit=1)
        params["q"] = f"PaymentId = {payment_id}"
        data = await self._fetch("payablesPayments", params)
        items = data.get("items", [])
        return items[0] if items else None

    async def search_journal_batches(self, period=None, status=None, source=None, q=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if period: conditions.append(f"DefaultPeriodName = '{period}'")
        if status: conditions.append(f"Status = '{status}'")
        if source: conditions.append(f"UserJeSourceName = '{source}'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=JOURNAL_BATCH_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("journalBatches", params)
        records = self._map_fields(data.get("items", []), JOURNAL_BATCH_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def search_gl_balances(self, ledger="", account_combination="", period="", currency="", mode="Detail", limit=25, offset=0):
        finder = (f"AccountBalanceFinder;accountCombination={account_combination},mode={mode},"
                  f"accountingPeriod={period},currency={currency},ledgerName={ledger}")
        params = self._build_params(fields=GL_BALANCE_DEFAULT_FIELDS, limit=limit, offset=offset, total_results=True)
        params["finder"] = finder
        data = await self._fetch("ledgerBalances", params)
        records = self._map_fields(data.get("items", []), GL_BALANCE_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def list_ledgers(self, name=None, ledger_type=None, q=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if name: conditions.append(f"LedgerName LIKE '*{name}*'")
        if ledger_type: conditions.append(f"LedgerType = '{ledger_type}'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=LEDGER_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("ledgersLOV", params)
        records = self._map_fields(data.get("items", []), LEDGER_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def list_chart_of_accounts(self, name=None, q=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if name: conditions.append(f"Name LIKE '*{name}*'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=CHART_OF_ACCOUNTS_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("chartOfAccountsLOV", params)
        records = self._map_fields(data.get("items", []), CHART_OF_ACCOUNTS_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def search_currency_rates(self, from_currency="", to_currency="", conversion_type="Corporate", start_date=None, end_date=None, limit=25, offset=0):
        finder_parts = []
        if from_currency: finder_parts.append(f"fromCurrency={from_currency}")
        if to_currency: finder_parts.append(f"toCurrency={to_currency}")
        if conversion_type: finder_parts.append(f"userConversionType={conversion_type}")
        if start_date: finder_parts.append(f"startDate={start_date}")
        if end_date: finder_parts.append(f"endDate={end_date}")
        params = self._build_params(limit=limit, offset=offset, total_results=True)
        if finder_parts:
            params["finder"] = f"CurrencyRatesFinder;{','.join(finder_parts)}"
        data = await self._fetch("currencyRates", params)
        records = self._map_fields(data.get("items", []), CURRENCY_RATE_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def list_payment_terms(self, name=None, q=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if name: conditions.append(f"name LIKE '*{name}*'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=PAYMENT_TERMS_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("payablesPaymentTerms", params)
        records = self._map_fields(data.get("items", []), PAYMENT_TERMS_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def search_approved_suppliers(self, supplier=None, item=None, status=None, procurement_bu=None, q=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if supplier: conditions.append(f"Supplier LIKE '*{supplier}*'")
        if item: conditions.append(f"Item LIKE '*{item}*'")
        if status: conditions.append(f"Status = '{status}'")
        if procurement_bu: conditions.append(f"ProcurementBU = '{procurement_bu}'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=APPROVED_SUPPLIER_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("procurementApprovedSupplierListEntries", params)
        records = self._map_fields(data.get("items", []), APPROVED_SUPPLIER_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def search_categories(self, name=None, category_type=None, q=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if name: conditions.append(f"CategoryName LIKE '*{name}*'")
        if category_type: conditions.append(f"CategoryType = '{category_type}'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=BROWSING_CATEGORY_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("browsingCategories", params)
        records = self._map_fields(data.get("items", []), BROWSING_CATEGORY_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def search_ar_invoices(self, customer=None, business_unit=None, date_from=None, date_to=None, status=None, q=None, limit=25, offset=0):
        finder_parts = []
        if customer: finder_parts.append(f"BillToCustomerName={customer}")
        if business_unit: finder_parts.append(f"BusinessUnit={business_unit}")
        conditions = []
        if q: conditions.append(q)
        if date_from: conditions.append(f"CreationDate >= '{date_from}'")
        if date_to: conditions.append(f"CreationDate <= '{date_to}'")
        if status: conditions.append(f"InvoiceStatus = '{status}'")
        has_filters = bool(conditions or finder_parts)
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=AR_INVOICE_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=has_filters)
        if finder_parts:
            params["finder"] = f"invoiceSearch;{','.join(finder_parts)}"
            if status:
                params["finder"] += f",InvoiceStatus={status}"
            params.pop("q", None)
        data = await self._fetch("receivablesInvoices", params)
        records = self._map_fields(data.get("items", []), AR_INVOICE_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def get_ar_invoice(self, transaction_id: int, expand_lines: bool = False) -> Optional[Dict]:
        params = self._build_params(limit=1)
        if expand_lines:
            params["expand"] = "receivablesInvoiceLines"
        params["q"] = f"CustomerTransactionId = {transaction_id}"
        data = await self._fetch("receivablesInvoices", params)
        items = data.get("items", [])
        return items[0] if items else None

    async def search_receipts(self, customer=None, date_from=None, date_to=None, receipt_number=None, business_unit=None, q=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if customer: conditions.append(f"CustomerName LIKE '*{customer}*'")
        if date_from: conditions.append(f"ReceiptDate >= '{date_from}'")
        if date_to: conditions.append(f"ReceiptDate <= '{date_to}'")
        if receipt_number: conditions.append(f"ReceiptNumber = '{receipt_number}'")
        if business_unit: conditions.append(f"BusinessUnit = '{business_unit}'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=RECEIPT_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("standardReceipts", params)
        records = self._map_fields(data.get("items", []), RECEIPT_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def search_expense_reports(self, employee=None, status=None, business_unit=None, date_from=None, date_to=None, q=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if employee: conditions.append(f"PersonName LIKE '*{employee}*'")
        if status: conditions.append(f"ExpenseReportStatus = '{status}'")
        if business_unit: conditions.append(f"BusinessUnit = '{business_unit}'")
        if date_from: conditions.append(f"ReportSubmitDate >= '{date_from}'")
        if date_to: conditions.append(f"ReportSubmitDate <= '{date_to}'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=EXPENSE_REPORT_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("expenseReports", params)
        records = self._map_fields(data.get("items", []), EXPENSE_REPORT_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def search_requisitions(self, preparer=None, status=None, business_unit=None, q=None, limit=25, offset=0):
        conditions = []
        if q: conditions.append(q)
        if preparer: conditions.append(f"Preparer LIKE '*{preparer}*'")
        if status: conditions.append(f"DocumentStatus = '{status}'")
        if business_unit: conditions.append(f"RequisitioningBU = '{business_unit}'")
        query = ";".join(conditions) if conditions else None
        params = self._build_params(fields=REQUISITION_DEFAULT_FIELDS, q=query, limit=limit, offset=offset, total_results=bool(conditions))
        data = await self._fetch("purchaseRequisitions", params)
        records = self._map_fields(data.get("items", []), REQUISITION_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def search_receiving_receipts(self, receipt_number="", limit=25, offset=0):
        params = self._build_params(fields=RECEIVING_RECEIPT_DEFAULT_FIELDS, limit=limit, offset=offset, total_results=True)
        params["q"] = f"ReceiptNumber = '{receipt_number}'"
        data = await self._fetch("receivingReceiptRequests", params)
        records = self._map_fields(data.get("items", []), RECEIVING_RECEIPT_FIELD_MAP)
        return records, data.get("hasMore", False), data.get("totalResults")

    async def get_supplier_details(self, supplier_id: int) -> Optional[Dict]:
        params = self._build_params(limit=1)
        params["expand"] = "sites,contacts,addresses"
        params["q"] = f"SupplierId = {supplier_id}"
        data = await self._fetch("suppliers", params)
        items = data.get("items", [])
        return items[0] if items else None

    # Write operations

    async def create_purchase_order(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("draftPurchaseOrders", body)

    async def update_po_distribution(self, po_header_id, line_id, schedule_id, distribution_id, updates):
        endpoint = (f"draftPurchaseOrders/{po_header_id}/child/lines/{line_id}"
                    f"/child/schedules/{schedule_id}/child/distributions/{distribution_id}")
        return await self._patch(endpoint, updates)

    async def change_po_status(self, po_header_id: int, action: str) -> Dict[str, Any]:
        action_map = {"CLOSE": "close", "CANCEL": "cancel", "FREEZE": "freeze", "HOLD": "hold",
                      "UNFREEZE": "unfreeze", "RELEASE HOLD": "removeHold", "REOPEN": "reopen"}
        action_name = action_map.get(action.upper())
        if not action_name:
            raise ValueError(f"Unknown PO action: {action}. Valid: {list(action_map.keys())}")
        return await self._post_action(f"purchaseOrders/{po_header_id}/action/{action_name}")

    async def create_invoice(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("invoices", body)

    async def change_invoice_status(self, invoice_id: int, action: str, reason: Optional[str] = None) -> Dict[str, Any]:
        action_map = {"CANCEL": "cancelInvoice", "VALIDATE": "validateInvoice"}
        action_name = action_map.get(action.upper())
        if not action_name:
            raise ValueError(f"Unknown invoice action: {action}. Valid: {list(action_map.keys())}")
        body: Dict[str, Any] = {"InvoiceId": invoice_id}
        if reason:
            body["ActionReason"] = reason
        return await self._post_action(f"invoices/action/{action_name}", body)

    async def create_requisition(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("purchaseRequisitions", body)

    async def change_requisition_status(self, requisition_id: int, action: str) -> Dict[str, Any]:
        action_map = {"WITHDRAW": "withdraw", "CANCEL": "cancel"}
        action_name = action_map.get(action.upper())
        if not action_name:
            raise ValueError(f"Unknown requisition action: {action}. Valid: {list(action_map.keys())}")
        return await self._post_action(f"purchaseRequisitions/{requisition_id}/action/{action_name}")

    def _map_fields(self, records: List[Dict], field_map: Dict[str, str]) -> List[Dict]:
        """Rename Oracle field names to internal names."""
        mapped = []
        for record in records:
            row = {}
            for oracle_key, internal_key in field_map.items():
                if oracle_key in record:
                    row[internal_key] = record[oracle_key]
            mapped.append(row)
        return mapped

    async def close(self):
        pass  # httpx clients are created per-request
