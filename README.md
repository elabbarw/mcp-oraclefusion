# mcp-oraclefusion

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server for Oracle Fusion Cloud ERP. Gives any MCP-compatible AI client (Claude, Cursor, Windsurf, etc.) read-only access to your Oracle Fusion data via STDIO transport.

**Authentication:** Basic Auth, Oracle JWT, (WIP: OAuth via Microsoft Entra ID)

## Quick start

Install and run via `uvx`:

```json
{
  "mcpServers": {
    "oracle-fusion": {
      "command": "uvx",
      "args": ["mcp-oraclefusion"],
      "env": {
        "ORACLE_FUSION_BASE_URL": "https://your-oracle-instance.fa.ocs.oraclecloud.com",
        "ORACLE_USERNAME": "your.name@example.com",
        "ORACLE_PASSWORD": "your_oracle_password"
      }
    }
  }
}
```

Or run directly:

```bash
pip install mcp-oraclefusion
export ORACLE_FUSION_BASE_URL=https://your-oracle-instance.fa.ocs.oraclecloud.com
export ORACLE_USERNAME=your.name@example.com
export ORACLE_PASSWORD=your_oracle_password
mcp-oraclefusion
```

## What you can do

Ask natural-language questions about your Oracle Fusion data:

- *"Show me all invoices from Google in Q1 2025"*
- *"Find open purchase orders from Dell over $50,000"*
- *"What's the USD to EUR corporate exchange rate for January 2025?"*
- *"Search requisitions pending approval in US Operations"*
- *"Look up supplier details for ACME Corp including sites and contacts"*
- *"Show AR invoices for customer XYZ"*
- *"Test the Oracle connection and show record counts"*
- *"What's the total invoice amount from Google this quarter?"*
- *"Break down AP spend by supplier, top 10"*
- *"What percentage of total spend is each business unit?"*

## Tools (30 read + 7 write)

### Accounts Payable
`search_invoices`, `get_invoice_details`, `search_payments`, `get_payment_details`, `list_payment_terms`

### Procurement
`search_purchase_orders`, `get_po_details`, `search_suppliers`, `get_supplier_details`, `search_requisitions`, `search_receiving_receipts`, `search_approved_suppliers`, `search_categories`

### General Ledger
`search_journal_batches`, `search_gl_balances`, `list_ledgers`, `list_chart_of_accounts`, `search_currency_rates`

### Accounts Receivable
`search_ar_invoices`, `get_ar_invoice_details`, `search_receipts`

### Expenses & HCM
`search_expense_reports`, `search_user_accounts`

### Infrastructure
`test_oracle_connection`

### Math / Aggregation
`aggregate_records`, `sumif_records`, `group_by_aggregate`, `lookup_record`, `percentage_of_total`, `safe_divide`

These tools run locally — no Oracle API calls. They use Python `Decimal` arithmetic to avoid float drift on currency values. The LLM fetches records with the search tools above, then passes them to these tools for exact computation (sums, averages, conditional aggregation, group-by pivots, percentages, ratios).

### Write tools (set `MCP_MODE=full` to enable)
`create_purchase_order`, `update_po_distribution`, `change_po_status`, `create_invoice`, `change_invoice_status`, `create_requisition`, `change_requisition_status`

## Configuration

| Env var | Required | Description |
|---------|----------|-------------|
| `ORACLE_FUSION_BASE_URL` | Yes | Your Oracle Fusion instance URL |
| `ORACLE_USERNAME` | Yes | Your Oracle Fusion username (email) |
| `ORACLE_PASSWORD` | If no JWT | Your Oracle Fusion password |
| `ORACLE_FUSION_API_VERSION` | No | REST API version (default `11.13.18.05`) |
| `MCP_MODE` | No | `readonly` (default) or `full` (enables write tools) |
| `LOG_LEVEL` | No | `WARNING` (default), `INFO`, `DEBUG` — logs go to stderr |

### OAuth / Microsoft Entra ID (coming soon)

OAuth login via Microsoft Entra ID is supported for multi-user deployments where each user authenticates with their corporate identity. This is currently being tested internally and will be documented once validated.

### JWT authentication (alternative to password)

Instead of a password you can authenticate with an RSA private key + certificate registered in Oracle's Security Console (API Authentication). Set these env vars and omit `ORACLE_PASSWORD`:

| Env var | Description |
|---------|-------------|
| `ORACLE_JWT_PRIVATE_KEY_PATH` | Path to the RSA private key PEM file |
| `ORACLE_JWT_PRIVATE_KEY` | Inline PEM key (alternative to path, useful in containers) |
| `ORACLE_JWT_CERT_PATH` | Path to the matching X.509 certificate PEM file |
| `ORACLE_JWT_ISSUER` | Trusted issuer value configured in Oracle |

The server tries JWT first and falls back to Basic Auth if the JWT vars are not set.

## Oracle REST API notes

- Query filters use Oracle syntax: conditions joined with `;` (AND), string matching with `LIKE '*term*'`
- Some fields are not queryable (`x-queryable: false`) — the server uses finders or client-side filtering
- CLOB fields are excluded from collection projections to avoid Oracle 500 errors
- The server auto-retries Oracle 500s by progressively stripping `totalResults` and `fields` params
- Status changes use Oracle action endpoints (`POST /resource/{id}/action/{name}`), not PATCH
- Supplier names are UPPERCASE in Oracle
- Pagination via `limit`/`offset`; `hasMore` indicates additional pages

## Requirements

- Python 3.10+
- Oracle Fusion Cloud instance with REST API access and a user account

## Author

Wanis Elabbar

## License

MIT
