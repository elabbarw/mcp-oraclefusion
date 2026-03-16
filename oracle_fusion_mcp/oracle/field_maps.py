"""Oracle Fusion REST API field name mappings"""

INVOICE_FIELD_MAP = {
    "InvoiceId": "invoice_id",
    "InvoiceNumber": "invoice_number",
    "InvoiceCurrency": "currency",
    "InvoiceAmount": "amount",
    "InvoiceDate": "invoice_date",
    "BusinessUnit": "business_unit",
    "Supplier": "vendor_name",
    "SupplierNumber": "vendor_code",
    "SupplierSite": "supplier_site",
    "PurchaseOrderNumber": "po_number",
    "Description": "description",
    "PaymentTerms": "payment_terms",
    "AccountingDate": "accounting_date",
    "ValidationStatus": "validation_status",
    "ApprovalStatus": "approval_status",
    "PaidStatus": "paid_status",
    "AccountingStatus": "accounting_status",
    "LegalEntity": "legal_entity",
    "LiabilityDistribution": "gl_combination",
    "InvoiceType": "invoice_type",
    "InvoiceSource": "invoice_source",
    "PaymentMethod": "payment_method",
    "CreationDate": "creation_date",
    "AmountPaid": "amount_paid",
}

PO_FIELD_MAP = {
    "POHeaderId": "po_header_id",
    "OrderNumber": "po_number",
    "ProcurementBU": "business_unit",
    "Supplier": "vendor_name",
    "Status": "status",
    "Description": "description",
    "CurrencyCode": "currency",
    "Total": "amount",
    "Buyer": "buyer",
    "RequesterDisplayName": "requester",
    "PaymentTerms": "payment_terms",
    "CreationDate": "creation_date",
}

SUPPLIER_FIELD_MAP = {
    "SupplierId": "supplier_id",
    "Supplier": "supplier_name",
    "SupplierNumber": "supplier_number",
    "SupplierType": "supplier_type",
    "Status": "status",
    "TaxpayerId": "taxpayer_id",
    "TaxpayerCountry": "taxpayer_country",
    "CreationDate": "creation_date",
}

PAYMENT_FIELD_MAP = {
    "PaymentId": "payment_id",
    "PaymentNumber": "payment_number",
    "PaymentDate": "payment_date",
    "PaymentAmount": "amount",
    "PaymentCurrency": "currency",
    "PaymentStatus": "status",
    "Payee": "payee_name",
    "SupplierNumber": "supplier_number",
    "PaymentMethod": "payment_method",
    "DisbursementBankAccountName": "bank_account",
    "PaperDocumentNumber": "document_number",
    "CheckId": "check_id",
    "CreationDate": "creation_date",
    "BusinessUnit": "business_unit",
    "LegalEntity": "legal_entity",
    "AccountingStatus": "accounting_status",
}

JOURNAL_BATCH_FIELD_MAP = {
    "JeBatchId": "batch_id",
    "BatchName": "batch_name",
    "DefaultPeriodName": "period",
    "Status": "status",
    "StatusMeaning": "status_meaning",
    "BatchDescription": "description",
    "PostedDate": "posted_date",
    "CreationDate": "creation_date",
    "UserJeSourceName": "source",
    "RunningTotalAccountedDr": "total_debit",
    "RunningTotalAccountedCr": "total_credit",
    "ApprovalStatusMeaning": "approval_status",
    "CompletionStatusMeaning": "completion_status",
    "ChartOfAccountsName": "chart_of_accounts",
}

GL_BALANCE_FIELD_MAP = {
    "LedgerName": "ledger",
    "PeriodName": "period",
    "Currency": "currency",
    "AccountCombination": "account_combination",
    "DetailAccountCombination": "detail_account_combination",
    "BeginningBalance": "beginning_balance",
    "PeriodActivity": "period_activity",
    "EndingBalance": "ending_balance",
    "AmountType": "amount_type",
    "CurrencyType": "currency_type",
    "Scenario": "scenario",
}

AR_INVOICE_FIELD_MAP = {
    "CustomerTransactionId": "transaction_id",
    "TransactionNumber": "transaction_number",
    "TransactionDate": "transaction_date",
    "TransactionType": "transaction_type",
    "BusinessUnit": "business_unit",
    "BillToCustomerName": "customer_name",
    "BillToCustomerNumber": "customer_number",
    "EnteredAmount": "amount",
    "InvoiceBalanceAmount": "balance_due",
    "InvoiceCurrencyCode": "currency",
    "InvoiceStatus": "status",
    "DueDate": "due_date",
    "Comments": "description",
    "PaymentTerms": "payment_terms",
    "CreationDate": "creation_date",
    "CrossReference": "cross_reference",
    "AccountingDate": "accounting_date",
}

RECEIPT_FIELD_MAP = {
    "StandardReceiptId": "receipt_id",
    "ReceiptNumber": "receipt_number",
    "ReceiptDate": "receipt_date",
    "Amount": "amount",
    "Currency": "currency",
    "Status": "status",
    "CustomerName": "customer_name",
    "CustomerAccountNumber": "customer_account_number",
    "ReceiptMethod": "receipt_method",
    "Comments": "comments",
    "CreationDate": "creation_date",
    "BusinessUnit": "business_unit",
    "State": "state",
}

REQUISITION_FIELD_MAP = {
    "RequisitionHeaderId": "requisition_id",
    "Requisition": "requisition_number",
    "Description": "description",
    "DocumentStatus": "status",
    "DocumentStatusCode": "status_code",
    "Preparer": "preparer",
    "PreparerEmail": "preparer_email",
    "CreationDate": "creation_date",
    "FunctionalCurrencyCode": "currency",
    "RequisitioningBU": "business_unit",
    "SubmissionDate": "submission_date",
    "ApprovedDate": "approved_date",
    "Justification": "justification",
}

RECEIVING_RECEIPT_FIELD_MAP = {
    "ReceiptHeaderId": "receipt_header_id",
    "ReceiptNumber": "receipt_number",
    "ShipmentNumber": "shipment_number",
    "VendorName": "supplier",
    "VendorSiteCode": "supplier_site",
    "OrganizationCode": "organization",
    "ReceiptSourceCode": "receipt_source",
    "ShippedDate": "shipped_date",
    "ExpectedReceiptDate": "expected_receipt_date",
    "Comments": "comments",
    "FreightCarrierName": "carrier",
    "BillOfLading": "bill_of_lading",
    "PackingSlip": "packing_slip",
    "WaybillAirbillNumber": "waybill",
    "GLDate": "gl_date",
}

EXPENSE_REPORT_FIELD_MAP = {
    "ExpenseReportId": "expense_report_id",
    "ExpenseReportNumber": "report_number",
    "ExpenseReportStatus": "status",
    "PersonName": "employee_name",
    "ReportSubmitDate": "submitted_date",
    "ExpenseReportTotal": "total_amount",
    "ReimbursementCurrencyCode": "currency",
    "BusinessUnit": "business_unit",
    "ExpenseStatusCode": "status_code",
    "CreationDate": "creation_date",
    "Purpose": "purpose",
}

INVOICE_DEFAULT_FIELDS = list(INVOICE_FIELD_MAP.keys())
PO_DEFAULT_FIELDS = [k for k in PO_FIELD_MAP if k != "RequesterDisplayName"]
SUPPLIER_DEFAULT_FIELDS = list(SUPPLIER_FIELD_MAP.keys())
PAYMENT_DEFAULT_FIELDS = list(PAYMENT_FIELD_MAP.keys())
JOURNAL_BATCH_DEFAULT_FIELDS = list(JOURNAL_BATCH_FIELD_MAP.keys())
GL_BALANCE_DEFAULT_FIELDS = list(GL_BALANCE_FIELD_MAP.keys())
AR_INVOICE_DEFAULT_FIELDS = [k for k in AR_INVOICE_FIELD_MAP if k != "Comments"]
_RECEIPT_SKIP_PROJECTION = {"Comments", "Status", "State"}
RECEIPT_DEFAULT_FIELDS = [k for k in RECEIPT_FIELD_MAP if k not in _RECEIPT_SKIP_PROJECTION]
REQUISITION_DEFAULT_FIELDS = list(REQUISITION_FIELD_MAP.keys())
RECEIVING_RECEIPT_DEFAULT_FIELDS = [k for k in RECEIVING_RECEIPT_FIELD_MAP if k != "Comments"]
EXPENSE_REPORT_DEFAULT_FIELDS = list(EXPENSE_REPORT_FIELD_MAP.keys())

LEDGER_FIELD_MAP = {
    "LedgerName": "ledger_name",
    "LedgerShortName": "ledger_short_name",
    "LedgerType": "ledger_type",
    "CurrencyCode": "currency",
    "ChartOfAccountsStructureId": "chart_of_accounts_id",
    "AccountingCalendar": "accounting_calendar",
    "BudgetaryControlEnabledFlag": "budgetary_control_enabled",
}
LEDGER_DEFAULT_FIELDS = list(LEDGER_FIELD_MAP.keys())

CHART_OF_ACCOUNTS_FIELD_MAP = {
    "StructureInstanceId": "structure_id",
    "StructureInstanceNumber": "structure_number",
    "StructureInstanceCode": "structure_code",
    "Name": "name",
    "Description": "description",
    "EnabledFlag": "enabled",
}
CHART_OF_ACCOUNTS_DEFAULT_FIELDS = list(CHART_OF_ACCOUNTS_FIELD_MAP.keys())

CURRENCY_RATE_FIELD_MAP = {
    "FromCurrency": "from_currency",
    "ToCurrency": "to_currency",
    "ConversionDate": "conversion_date",
    "ConversionRate": "conversion_rate",
    "ConversionType": "conversion_type",
    "UserConversionType": "user_conversion_type",
}

PAYMENT_TERMS_FIELD_MAP = {
    "termsId": "terms_id",
    "name": "name",
    "description": "description",
    "enabledFlag": "enabled",
    "fromDate": "from_date",
    "toDate": "to_date",
    "cutoffDay": "cutoff_day",
    "rank": "rank",
}
PAYMENT_TERMS_DEFAULT_FIELDS = list(PAYMENT_TERMS_FIELD_MAP.keys())

APPROVED_SUPPLIER_FIELD_MAP = {
    "AslId": "asl_id",
    "Supplier": "supplier",
    "SupplierId": "supplier_id",
    "SupplierSite": "supplier_site",
    "Item": "item",
    "Status": "status",
    "Scope": "scope",
    "ProcurementBU": "procurement_bu",
    "ShipToOrganization": "ship_to_organization",
    "DisableFlag": "disabled",
    "Comments": "comments",
    "PrimaryVendorItem": "vendor_item",
    "PurchasingUOM": "purchasing_uom",
    "MinimumOrderQuantity": "minimum_order_qty",
}
APPROVED_SUPPLIER_DEFAULT_FIELDS = [
    k for k in APPROVED_SUPPLIER_FIELD_MAP if k != "Comments"
]

BROWSING_CATEGORY_FIELD_MAP = {
    "CategoryId": "category_id",
    "CategoryName": "category_name",
    "CategoryType": "category_type",
    "Description": "description",
}
BROWSING_CATEGORY_DEFAULT_FIELDS = list(BROWSING_CATEGORY_FIELD_MAP.keys())

USER_ACCOUNT_FIELD_MAP = {
    "UserId": "user_id",
    "Username": "username",
    "GUID": "guid",
    "PersonId": "person_id",
    "PersonNumber": "person_number",
    "SuspendedFlag": "suspended",
    "CreationDate": "creation_date",
}
USER_ACCOUNT_DEFAULT_FIELDS = list(USER_ACCOUNT_FIELD_MAP.keys())
