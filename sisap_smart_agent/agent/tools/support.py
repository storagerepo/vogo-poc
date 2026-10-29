"""
Function tools for the Technical Support workflow: troubleshooting,
diagnostics, tickets, escalation, and resolution.

Guardrail note: create_ticket and escalate_to_human are state-changing.
The system prompt instructs the agent to get an explicit verbal "yes"
BEFORE calling these — this file does not enforce that itself (it can't
observe the conversation), so the instructions.py guardrail text is
load-bearing here.
"""

from __future__ import annotations

from livekit.agents import function_tool, RunContext

from . import data_store


@function_tool()
async def record_troubleshooting_step_tool(
    context: RunContext,
    step: str,
    device: str | None = None,
    error_message: str | None = None,
) -> dict:
    """Remember what the user already tried plus their device and exact error, so a ticket can include them.

    Args:
        step: One step the user has already tried, e.g. "Restarted VPN application".
        device: The user's device, e.g. "Windows laptop".
        error_message: The exact error text the user sees.
    """
    state = context.userdata
    denied = data_store.check_access(state, "record_troubleshooting_step")
    if denied:
        return {"ok": False, "error": denied}

    if step and step.strip():
        state.steps_tried.append(step.strip())
    state.device = device or state.device
    state.error_message = error_message or state.error_message
    return {"ok": True, "steps_tried": state.steps_tried, "device": state.device, "error_message": state.error_message}


@function_tool()
async def run_diagnostic_tool(
    context: RunContext,
    check_type: str,
    target: str,
) -> dict:
    """Run a SAFE, simulated diagnostic on an approved target.

    Args:
        check_type: One of connectivity, vpn_service, dns_resolution, port_check.
        target: Approved hostname, e.g. vpn.mock-sisap.test. For port_check use host:port, e.g. vpn.mock-sisap.test:4500.
    """
    state = context.userdata
    denied = data_store.check_access(state, "run_diagnostic")
    if denied:
        return {"ok": False, "error": denied}

    try:
        result = data_store.run_diagnostic(check_type, target)
    except data_store.SisapError as exc:
        return {"ok": False, "error": str(exc)}

    state.diagnostics_run.append(result)
    return {"ok": True, **result}


@function_tool()
async def create_ticket_tool(
    context: RunContext,
    issue: str,
    priority: str = "Medium",
    user_confirmed: bool = False,
) -> dict:
    """Create a support ticket from the collected context (device, error, steps tried, diagnostics). Requires explicit user confirmation.

    Args:
        issue: Short description of the problem.
        priority: Low, Medium, High or Critical.
        user_confirmed: True only after the user explicitly agreed to create the ticket.
    """
    state = context.userdata
    denied = data_store.check_access(state, "create_ticket")
    if denied:
        return {"ok": False, "error": denied}

    draft = {
        "issue": issue, "device": state.device, "error": state.error_message,
        "steps_tried": state.steps_tried, "priority": priority, "diagnostics": state.diagnostics_run,
    }
    if not user_confirmed:
        return {"ok": False, "needs_confirmation": True, "draft": draft,
                "instruction": "Read the draft back to the user and ask for explicit confirmation, then call again with user_confirmed=true."}

    try:
        ticket = data_store.create_ticket(
            issue=issue, device=state.device, error=state.error_message, steps_tried=state.steps_tried,
            priority=priority, requester=state.user_name, diagnostics=state.diagnostics_run,
        )
    except data_store.SisapError as exc:
        return {"ok": False, "error": str(exc)}

    state.active_ticket_id = ticket["ticket_id"]
    return {"ok": True, "ticket": ticket}


@function_tool()
async def get_ticket_status_tool(
    context: RunContext,
    ticket_id: str,
) -> dict:
    """Look up the current status of an existing ticket.

    Args:
        ticket_id: Ticket ID such as TKT-001.
    """
    state = context.userdata
    denied = data_store.check_access(state, "get_ticket_status")
    if denied:
        return {"ok": False, "error": denied}

    try:
        t = data_store.get_ticket(ticket_id)
    except data_store.SisapError as exc:
        return {"ok": False, "error": str(exc)}

    state.active_ticket_id = t["ticket_id"]
    return {"ok": True, "ticket_id": t["ticket_id"], "issue": t["issue"], "status": t["status"],
            "priority": t["priority"], "assigned_team": t["assigned_team"], "steps_tried": t["steps_tried"]}


@function_tool()
async def escalate_to_human_tool(
    context: RunContext,
    summary: str,
    ticket_id: str | None = None,
    user_confirmed: bool = False,
) -> dict:
    """Hand an unresolved ticket to a human engineer. Requires explicit user confirmation.

    Args:
        summary: English summary for the engineer: problem, what was tried, diagnostic findings.
        ticket_id: Ticket to escalate. Defaults to the ticket in this conversation.
        user_confirmed: True only after the user explicitly agreed to escalate.
    """
    state = context.userdata
    denied = data_store.check_access(state, "escalate_to_human")
    if denied:
        return {"ok": False, "error": denied}

    tid = ticket_id or state.active_ticket_id
    if not tid:
        return {"ok": False, "error": "No ticket to escalate. Create a ticket first."}
    if not user_confirmed:
        return {"ok": False, "needs_confirmation": True,
                "instruction": f"Ask the user to confirm escalating {tid} to a human engineer, then call again with user_confirmed=true."}

    try:
        t = data_store.escalate_ticket(tid, summary)
    except data_store.SisapError as exc:
        return {"ok": False, "error": str(exc)}

    return {"ok": True, "ticket_id": t["ticket_id"], "status": t["status"], "assigned_team": t["assigned_team"], "handoff": t["handoff"]}


@function_tool()
async def confirm_resolution_tool(
    context: RunContext,
    user_says_resolved: bool,
    ticket_id: str | None = None,
) -> dict:
    """Record the outcome AFTER the user has tested and told you whether the problem is fixed.

    Args:
        user_says_resolved: True only if the user said the problem is gone.
        ticket_id: Optional ticket to mark Resolved.
    """
    state = context.userdata
    denied = data_store.check_access(state, "confirm_resolution")
    if denied:
        return {"ok": False, "error": denied}

    state.resolved = user_says_resolved
    tid = ticket_id or state.active_ticket_id

    if user_says_resolved and tid:
        try:
            data_store.set_ticket_status(tid, "Resolved")
        except data_store.SisapError as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "resolved": True, "ticket_id": tid, "status": "Resolved"}

    return {"ok": True, "resolved": user_says_resolved,
            "instruction": None if user_says_resolved else "Issue is not resolved: continue troubleshooting, or create a ticket / escalate."}
