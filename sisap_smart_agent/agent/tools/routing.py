"""Workflow routing tool — determines whether the user needs Technical Support or SOC Copilot."""

from __future__ import annotations

from livekit.agents import function_tool, RunContext

from . import data_store


@function_tool()
async def route_request_tool(
    context: RunContext,
    user_request_in_english: str,
) -> dict:
    """Choose the workflow (technical support or SOC investigation) for the user's request. Call this first for every new task.

    Args:
        user_request_in_english: A short English summary of what the user asked, keeping any IDs (TKT-001, ALT-001, user101) unchanged.
    """
    state = context.userdata
    decision = data_store.classify_request(user_request_in_english)

    if decision.workflow == data_store.CLARIFY:
        return {
            "ok": True,
            "workflow": state.workflow or data_store.CLARIFY,
            "action": "clarify",
            "instruction": "Intent is unclear. Ask the user what issue they need help with "
                           "(a technical problem such as VPN/network, or a security alert investigation). Do not call other tools yet.",
        }

    switched = state.workflow is not None and state.workflow != decision.workflow
    if state.workflow != decision.workflow:
        state.reset_task()
        state.workflow = decision.workflow

    result = {
        "ok": True,
        "workflow": state.workflow,
        "switched_from_previous": switched,
        "suggested_first_tool": decision.first_tool,
        "reason": decision.reason,
    }
    if decision.missing_id:
        result["action"] = "ask_for_id"
        result["instruction"] = "The required ID is missing. Ask the user for the alert ID (for example ALT-001) before calling get_alert_details."
    return result
