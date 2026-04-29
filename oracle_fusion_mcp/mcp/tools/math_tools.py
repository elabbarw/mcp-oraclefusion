"""Deterministic math tools for aggregating Oracle Fusion records.

All numeric operations use Python's Decimal to avoid float drift on
currency values. These tools operate on records already fetched by
other tools — they never call Oracle directly.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from collections import defaultdict

from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...oracle.client import OracleClient
from ._helpers import _text_result

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_decimal(val: Any) -> Optional[Decimal]:
    """Convert a value to Decimal, returning None if not numeric."""
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _quantize(val: Decimal, decimal_places: int) -> str:
    """Quantize a Decimal and return as string."""
    q = Decimal(10) ** -decimal_places
    return str(val.quantize(q, rounding=ROUND_HALF_UP))


def _extract_field(records: List[Dict], field: str) -> tuple:
    """Extract Decimal values from a field, tracking skips."""
    values = []
    skipped = 0
    for rec in records:
        raw = rec.get(field)
        d = _to_decimal(raw)
        if d is not None:
            values.append(d)
        else:
            skipped += 1
    return values, skipped


def _matches_condition(record_val: Any, operator: str, condition_val: Any) -> bool:
    """Evaluate a filter condition."""
    if record_val is None:
        return False
    if operator == "eq":
        return str(record_val) == str(condition_val)
    elif operator == "neq":
        return str(record_val) != str(condition_val)
    elif operator == "contains":
        return str(condition_val).lower() in str(record_val).lower()
    elif operator == "startswith":
        return str(record_val).lower().startswith(str(condition_val).lower())
    elif operator == "in":
        if isinstance(condition_val, list):
            return str(record_val) in [str(v) for v in condition_val]
        return False
    elif operator in ("gt", "gte", "lt", "lte"):
        left = _to_decimal(record_val)
        right = _to_decimal(condition_val)
        if left is None or right is None:
            return False
        if operator == "gt":
            return left > right
        elif operator == "gte":
            return left >= right
        elif operator == "lt":
            return left < right
        elif operator == "lte":
            return left <= right
    return False


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "aggregate_records",
        "description": (
            "Compute an aggregate (sum, avg, min, max, median, count, count_nonnull) "
            "over a numeric field in a list of records. Use this for ANY arithmetic on "
            "Oracle Fusion data — do NOT compute sums, averages, or counts yourself. "
            "All math uses exact Decimal arithmetic to avoid float drift on currency values."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "records": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of record objects from a previous search tool call.",
                },
                "field": {
                    "type": "string",
                    "description": "Field name to aggregate (e.g. 'InvoiceAmount', 'TotalAmount').",
                },
                "operation": {
                    "type": "string",
                    "enum": ["sum", "avg", "min", "max", "median", "count", "count_nonnull"],
                    "description": "Aggregation operation.",
                },
                "decimal_places": {
                    "type": "integer",
                    "default": 2,
                    "description": "Decimal places for rounding (default 2).",
                },
            },
            "required": ["records", "field", "operation"],
        },
    },
    {
        "name": "sumif_records",
        "description": (
            "Conditional aggregation — like Excel SUMIF/COUNTIF/AVERAGEIF. "
            "Sum, count, or average a field where a condition matches. "
            "Operators: eq, neq, gt, gte, lt, lte, contains, startswith, in."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "records": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of record objects.",
                },
                "sum_field": {
                    "type": "string",
                    "description": "Field to aggregate.",
                },
                "condition_field": {
                    "type": "string",
                    "description": "Field to test the condition against.",
                },
                "operator": {
                    "type": "string",
                    "enum": ["eq", "neq", "gt", "gte", "lt", "lte", "contains", "startswith", "in"],
                    "description": "Comparison operator.",
                },
                "condition_value": {
                    "description": "Value to compare against. Use an array for 'in' operator.",
                },
                "operation": {
                    "type": "string",
                    "enum": ["sum", "avg", "count"],
                    "default": "sum",
                    "description": "Aggregation on matched records (default: sum).",
                },
                "decimal_places": {
                    "type": "integer",
                    "default": 2,
                },
            },
            "required": ["records", "sum_field", "condition_field", "operator", "condition_value"],
        },
    },
    {
        "name": "group_by_aggregate",
        "description": (
            "Group records by a field and aggregate another field per group. "
            "Like a SQL GROUP BY or Excel pivot. Returns sorted results with "
            "optional limit. Use for subtotals by supplier, business unit, status, etc."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "records": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of record objects.",
                },
                "group_field": {
                    "type": "string",
                    "description": "Field to group by (e.g. 'SupplierName', 'BusinessUnit').",
                },
                "agg_field": {
                    "type": "string",
                    "description": "Field to aggregate within each group.",
                },
                "operation": {
                    "type": "string",
                    "enum": ["sum", "avg", "min", "max", "count"],
                    "default": "sum",
                    "description": "Aggregation operation (default: sum).",
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["value_desc", "value_asc", "key_asc", "key_desc"],
                    "default": "value_desc",
                    "description": "Sort order (default: value_desc = highest first).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of groups to return (e.g. top 10).",
                },
                "decimal_places": {
                    "type": "integer",
                    "default": 2,
                },
            },
            "required": ["records", "group_field", "agg_field"],
        },
    },
    {
        "name": "lookup_record",
        "description": (
            "Find a record by field value — like VLOOKUP/XLOOKUP. Returns the first "
            "match or all matches. Use for finding a specific invoice, supplier, etc."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "records": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of record objects.",
                },
                "field": {
                    "type": "string",
                    "description": "Field to search in.",
                },
                "value": {
                    "description": "Value to match.",
                },
                "operator": {
                    "type": "string",
                    "enum": ["eq", "contains", "startswith", "gt", "gte", "lt", "lte"],
                    "default": "eq",
                    "description": "Comparison operator (default: eq).",
                },
                "return_all": {
                    "type": "boolean",
                    "default": False,
                    "description": "Return all matches (true) or just first (false).",
                },
            },
            "required": ["records", "field", "value"],
        },
    },
    {
        "name": "percentage_of_total",
        "description": (
            "Calculate each record's or group's share of the total for a numeric field. "
            "Optionally group by a field first. Returns percentages that sum to 100."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "records": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of record objects.",
                },
                "value_field": {
                    "type": "string",
                    "description": "Numeric field to compute percentages for.",
                },
                "group_field": {
                    "type": "string",
                    "description": "Optional: group by this field before computing percentages.",
                },
                "decimal_places": {
                    "type": "integer",
                    "default": 2,
                },
            },
            "required": ["records", "value_field"],
        },
    },
    {
        "name": "safe_divide",
        "description": (
            "Divide two numbers with exact Decimal arithmetic. Returns null on "
            "divide-by-zero instead of erroring. Use for ratios, rates, per-unit costs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "numerator": {
                    "type": "number",
                    "description": "The dividend.",
                },
                "denominator": {
                    "type": "number",
                    "description": "The divisor.",
                },
                "decimal_places": {
                    "type": "integer",
                    "default": 2,
                },
            },
            "required": ["numerator", "denominator"],
        },
    },
]


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def handle_aggregate_records(
    request: Request, session: ValidatedUser,
    params: Dict[str, Any], oracle_client: Optional[OracleClient],
) -> Dict[str, Any]:
    records = params["records"]
    field = params["field"]
    op = params["operation"]
    dp = params.get("decimal_places", 2)

    if op == "count":
        return _text_result({
            "operation": "count",
            "field": field,
            "result": len(records),
            "rows_input": len(records),
        })

    values, skipped = _extract_field(records, field)

    if not values:
        return _text_result({
            "operation": op,
            "field": field,
            "result": None,
            "rows_input": len(records),
            "rows_used": 0,
            "rows_skipped_null_or_nonnumeric": skipped,
            "note": f"No numeric values found in field '{field}'.",
        })

    if op == "sum":
        result = sum(values)
    elif op == "avg":
        result = sum(values) / len(values)
    elif op == "min":
        result = min(values)
    elif op == "max":
        result = max(values)
    elif op == "median":
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        if n % 2 == 1:
            result = sorted_vals[n // 2]
        else:
            result = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    elif op == "count_nonnull":
        return _text_result({
            "operation": "count_nonnull",
            "field": field,
            "result": len(values),
            "rows_input": len(records),
            "rows_skipped_null_or_nonnumeric": skipped,
        })
    else:
        return _text_result({"error": f"Unknown operation: {op}"})

    return _text_result({
        "operation": op,
        "field": field,
        "result": _quantize(result, dp),
        "rows_input": len(records),
        "rows_used": len(values),
        "rows_skipped_null_or_nonnumeric": skipped,
    })


async def handle_sumif_records(
    request: Request, session: ValidatedUser,
    params: Dict[str, Any], oracle_client: Optional[OracleClient],
) -> Dict[str, Any]:
    records = params["records"]
    sum_field = params["sum_field"]
    cond_field = params["condition_field"]
    operator = params["operator"]
    cond_value = params["condition_value"]
    op = params.get("operation", "sum")
    dp = params.get("decimal_places", 2)

    matched = [r for r in records if _matches_condition(r.get(cond_field), operator, cond_value)]

    if op == "count":
        return _text_result({
            "operation": "count",
            "condition": f"{cond_field} {operator} {cond_value}",
            "result": len(matched),
            "rows_input": len(records),
            "rows_matched": len(matched),
        })

    values, skipped = _extract_field(matched, sum_field)

    if not values:
        return _text_result({
            "operation": op,
            "condition": f"{cond_field} {operator} {cond_value}",
            "result": None if op != "count" else 0,
            "rows_input": len(records),
            "rows_matched": len(matched),
            "rows_used": 0,
            "rows_skipped_null_or_nonnumeric": skipped,
        })

    if op == "sum":
        result = sum(values)
    elif op == "avg":
        result = sum(values) / len(values)
    else:
        return _text_result({"error": f"Unknown operation for sumif: {op}"})

    return _text_result({
        "operation": op,
        "condition": f"{cond_field} {operator} {cond_value}",
        "result": _quantize(result, dp),
        "rows_input": len(records),
        "rows_matched": len(matched),
        "rows_used": len(values),
        "rows_skipped_null_or_nonnumeric": skipped,
    })


async def handle_group_by_aggregate(
    request: Request, session: ValidatedUser,
    params: Dict[str, Any], oracle_client: Optional[OracleClient],
) -> Dict[str, Any]:
    records = params["records"]
    group_field = params["group_field"]
    agg_field = params["agg_field"]
    op = params.get("operation", "sum")
    sort_by = params.get("sort_by", "value_desc")
    limit = params.get("limit")
    dp = params.get("decimal_places", 2)

    groups: Dict[str, List[Decimal]] = defaultdict(list)
    group_counts: Dict[str, int] = defaultdict(int)
    skipped_total = 0

    for rec in records:
        key = str(rec.get(group_field, "(null)"))
        group_counts[key] += 1
        if op != "count":
            d = _to_decimal(rec.get(agg_field))
            if d is not None:
                groups[key].append(d)
            else:
                skipped_total += 1

    results = []
    all_keys = group_counts.keys() if op == "count" else groups.keys()
    for key in all_keys:
        vals = groups.get(key, [])
        if op == "sum":
            agg = sum(vals)
        elif op == "avg":
            agg = sum(vals) / len(vals) if vals else Decimal(0)
        elif op == "min":
            agg = min(vals) if vals else Decimal(0)
        elif op == "max":
            agg = max(vals) if vals else Decimal(0)
        elif op == "count":
            agg = Decimal(group_counts[key])
        else:
            return _text_result({"error": f"Unknown operation: {op}"})

        results.append({
            "group": key,
            "value": _quantize(agg, dp),
            "count": group_counts[key],
        })

    # Sort
    if sort_by == "value_desc":
        results.sort(key=lambda r: Decimal(r["value"]), reverse=True)
    elif sort_by == "value_asc":
        results.sort(key=lambda r: Decimal(r["value"]))
    elif sort_by == "key_asc":
        results.sort(key=lambda r: r["group"])
    elif sort_by == "key_desc":
        results.sort(key=lambda r: r["group"], reverse=True)

    if limit is not None:
        results = results[:limit]

    return _text_result({
        "operation": op,
        "group_field": group_field,
        "agg_field": agg_field,
        "groups": results,
        "total_groups": len(groups),
        "rows_input": len(records),
        "rows_skipped_null_or_nonnumeric": skipped_total,
    })


async def handle_lookup_record(
    request: Request, session: ValidatedUser,
    params: Dict[str, Any], oracle_client: Optional[OracleClient],
) -> Dict[str, Any]:
    records = params["records"]
    field = params["field"]
    value = params["value"]
    operator = params.get("operator", "eq")
    return_all = params.get("return_all", False)

    matched = [r for r in records if _matches_condition(r.get(field), operator, value)]

    if not matched:
        return _text_result({
            "result": None,
            "rows_searched": len(records),
            "rows_matched": 0,
        })

    if return_all:
        return _text_result({
            "result": matched,
            "rows_searched": len(records),
            "rows_matched": len(matched),
        })

    return _text_result({
        "result": matched[0],
        "rows_searched": len(records),
        "rows_matched": len(matched),
    })


async def handle_percentage_of_total(
    request: Request, session: ValidatedUser,
    params: Dict[str, Any], oracle_client: Optional[OracleClient],
) -> Dict[str, Any]:
    records = params["records"]
    value_field = params["value_field"]
    group_field = params.get("group_field")
    dp = params.get("decimal_places", 2)

    if group_field:
        # Group first, then compute percentages per group
        groups: Dict[str, Decimal] = defaultdict(lambda: Decimal(0))
        skipped = 0
        for rec in records:
            key = str(rec.get(group_field, "(null)"))
            d = _to_decimal(rec.get(value_field))
            if d is not None:
                groups[key] += d
            else:
                skipped += 1

        total = sum(groups.values())
        if total == 0:
            return _text_result({
                "result": [],
                "total": "0",
                "note": "Total is zero — cannot compute percentages.",
            })

        results = []
        for key, val in groups.items():
            pct = (val / total) * 100
            results.append({
                "group": key,
                "value": _quantize(val, dp),
                "percentage": _quantize(pct, dp),
            })

        results.sort(key=lambda r: Decimal(r["percentage"]), reverse=True)

        return _text_result({
            "result": results,
            "total": _quantize(total, dp),
            "rows_input": len(records),
            "rows_skipped_null_or_nonnumeric": skipped,
        })

    else:
        # Per-record percentages
        values_and_indices = []
        skipped = 0
        for i, rec in enumerate(records):
            d = _to_decimal(rec.get(value_field))
            if d is not None:
                values_and_indices.append((i, d))
            else:
                skipped += 1

        total = sum(v for _, v in values_and_indices)
        if total == 0:
            return _text_result({
                "result": [],
                "total": "0",
                "note": "Total is zero — cannot compute percentages.",
            })

        results = []
        for i, val in values_and_indices:
            pct = (val / total) * 100
            entry = dict(records[i])
            entry["_percentage"] = _quantize(pct, dp)
            results.append(entry)

        return _text_result({
            "result": results,
            "total": _quantize(total, dp),
            "rows_input": len(records),
            "rows_used": len(values_and_indices),
            "rows_skipped_null_or_nonnumeric": skipped,
        })


async def handle_safe_divide(
    request: Request, session: ValidatedUser,
    params: Dict[str, Any], oracle_client: Optional[OracleClient],
) -> Dict[str, Any]:
    dp = params.get("decimal_places", 2)
    num = _to_decimal(params["numerator"])
    den = _to_decimal(params["denominator"])

    if num is None or den is None:
        return _text_result({
            "result": None,
            "note": "Non-numeric input.",
        })

    if den == 0:
        return _text_result({
            "result": None,
            "numerator": str(num),
            "denominator": "0",
            "note": "Division by zero — result is null.",
        })

    result = num / den
    return _text_result({
        "result": _quantize(result, dp),
        "numerator": str(num),
        "denominator": str(den),
    })


HANDLERS = {
    "aggregate_records": handle_aggregate_records,
    "sumif_records": handle_sumif_records,
    "group_by_aggregate": handle_group_by_aggregate,
    "lookup_record": handle_lookup_record,
    "percentage_of_total": handle_percentage_of_total,
    "safe_divide": handle_safe_divide,
}
