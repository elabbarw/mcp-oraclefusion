"""
MCP Tools package for Oracle Fusion ERP.

Public API:
  - get_tools_list(mode) -> tool definitions filtered by MCP_MODE
  - handle_tool_call(request, session, tool_name, tool_arguments) -> MCP result
"""

import logging
from typing import Any, Dict

from oracle_fusion_mcp._types import Request
from ...auth.entra import ValidatedUser
from ...auth.oracle_jwt import get_oracle_jwt_signer
from ...config.settings import get_settings
from ...oracle.client import OracleClient
from ._helpers import _text_result

from .ap_tools import TOOLS as AP_TOOLS, HANDLERS as AP_HANDLERS
from .procurement_tools import TOOLS as PROC_TOOLS, HANDLERS as PROC_HANDLERS
from .gl_tools import TOOLS as GL_TOOLS, HANDLERS as GL_HANDLERS
from .ar_tools import TOOLS as AR_TOOLS, HANDLERS as AR_HANDLERS
from .expense_tools import TOOLS as EXPENSE_TOOLS, HANDLERS as EXPENSE_HANDLERS
from .hcm_tools import TOOLS as HCM_TOOLS, HANDLERS as HCM_HANDLERS
from .infra_tools import TOOLS as INFRA_TOOLS, HANDLERS as INFRA_HANDLERS
from .write_po_tools import TOOLS as WRITE_PO_TOOLS, HANDLERS as WRITE_PO_HANDLERS
from .write_ap_tools import TOOLS as WRITE_AP_TOOLS, HANDLERS as WRITE_AP_HANDLERS
from .write_req_tools import TOOLS as WRITE_REQ_TOOLS, HANDLERS as WRITE_REQ_HANDLERS

logger = logging.getLogger(__name__)

_READ_TOOLS = AP_TOOLS + PROC_TOOLS + GL_TOOLS + AR_TOOLS + EXPENSE_TOOLS + HCM_TOOLS + INFRA_TOOLS
_READ_HANDLERS: Dict[str, Any] = {
    **AP_HANDLERS, **PROC_HANDLERS, **GL_HANDLERS, **AR_HANDLERS,
    **EXPENSE_HANDLERS, **HCM_HANDLERS, **INFRA_HANDLERS,
}

_WRITE_TOOLS = WRITE_PO_TOOLS + WRITE_AP_TOOLS + WRITE_REQ_TOOLS
_WRITE_HANDLERS: Dict[str, Any] = {**WRITE_PO_HANDLERS, **WRITE_AP_HANDLERS, **WRITE_REQ_HANDLERS}
_WRITE_TOOL_NAMES = frozenset(_WRITE_HANDLERS.keys())
_ALL_HANDLERS: Dict[str, Any] = {**_READ_HANDLERS, **_WRITE_HANDLERS}


async def get_tools_list(mode: str = "readonly") -> Dict[str, Any]:
    """Return the list of available MCP tools, filtered by mode."""
    tools = list(_READ_TOOLS)
    if mode == "full":
        tools.extend(_WRITE_TOOLS)
    return {"tools": tools}


async def handle_tool_call(
    request: Request,
    session: ValidatedUser,
    tool_name: str,
    tool_arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """Dispatch an MCP tools/call request to the appropriate handler."""
    try:
        settings = get_settings()
        if tool_name in _WRITE_TOOL_NAMES and settings.MCP_MODE != "full":
            raise PermissionError(
                f"Tool '{tool_name}' requires MCP_MODE=full. Current mode is 'readonly'."
            )

        basic_auth = getattr(request.state, "basic_auth", None)
        oracle_jwt = getattr(request.state, "oracle_jwt", False)
        entra_bearer = getattr(request.state, "entra_bearer", False)
        if basic_auth:
            oracle_client = OracleClient(username=basic_auth[0], password=basic_auth[1])
        elif oracle_jwt or entra_bearer:
            jwt_signer = get_oracle_jwt_signer()
            if jwt_signer and session.email:
                oracle_token = jwt_signer.sign(session.email)
                oracle_client = OracleClient(bearer_token=oracle_token)
            else:
                return _text_result({"error": "Oracle JWT signer not configured. Use Basic Auth."})
        else:
            return _text_result({"error": "No Oracle credentials available. Set ORACLE_USERNAME and ORACLE_PASSWORD."})

        handler = _ALL_HANDLERS.get(tool_name)
        if not handler:
            return _text_result({"error": f"Tool '{tool_name}' not found"})

        return await handler(request, session, tool_arguments, oracle_client)

    except PermissionError:
        raise
    except Exception as error:
        logger.error(f"Error in tool {tool_name}: {error}", exc_info=True)
        return _text_result({"error": f"Error executing tool: {str(error)}"})
