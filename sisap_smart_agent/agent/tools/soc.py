"""
Function tools for the SOC Analyst Copilot workflow: alert inspection,
evidence search (auth + endpoint logs), correlation / timeline analysis,
investigation report generation, and analyst handoff.

Read-only on evidence; no response or containment actions exist.
"""

from __future__ import annotations

from datetime import timedelta
from livekit.agents import function_tool, RunContext

from . import data_store


def _fmt(dt) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


@function_tool()
async def get_alert_details_tool(
    context: RunContext,
    alert_id: str,
) -> dict:
    """Retrieve a security alert (severity, user, source IP, device, timestamp, description).

    Args:
        alert_id: Alert ID such as ALT-001.
    """
    state = context.userdata
    denied = data_store.check_access(state, "get_alert_details")
    if denied:
        return {"ok": False, "error": denied}

    try:
        alert = data_store.get_alert(alert_id)
    except data_store.SisapError as exc:
        return {"ok": False, "error": str(exc)}

    if not state.active_alert or state.active_alert["alert_id"] != alert["alert_id"]:
        state.retrieved_events, state.correlation = [], None
    state.active_alert = alert
    return {"ok": True, "alert": alert}


@function_tool()
async def search_security_logs_tool(
    context: RunContext,
    username: str | None = None,
    source_ip: str | None = None,
    device: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    event_type: str | None = None,
) -> dict:
    """Search authentication and endpoint logs. Matches records for the given user OR IP OR device.
    If no time range is given and an alert is loaded, a window around the alert is used.

    Args:
        username: Account name, e.g. user101.
        source_ip: Source IP address.
        device: Device name, e.g. LAPTOP-GT-014.
        start_time: ISO-8601 UTC start, e.g. 2026-10-27T08:40:00Z.
        end_time: ISO-8601 UTC end.
        event_type: Text to match in the event, e.g. "Login Failed".
    """
    state = context.userdata
    denied = data_store.check_access(state, "search_security_logs")
    if denied:
        return {"ok": False, "error": denied}

    # Default to a window around the active alert when the caller gives no time range.
    if state.active_alert and not (start_time or end_time):
        ts = data_store.parse_ts(state.active_alert["timestamp"])
        w = timedelta(minutes=data_store.LOG_WINDOW_MINUTES)
        start_time, end_time = _fmt(ts - w), _fmt(ts + w)

    try:
        events = data_store.search_logs(
            username=username,
            source_ip=source_ip,
            device=device,
            start=start_time,
            end=end_time,
            event_type=event_type,
        )
    except data_store.SisapError as exc:
        return {"ok": False, "error": str(exc)}

    # Only evidence for the active alert is accumulated for correlation.
    if state.active_alert:
        known = {e["event_id"] for e in state.retrieved_events}
        state.retrieved_events += [e for e in events if e["event_id"] not in known]
        state.correlation = None

    return {
        "ok": True,
        "count": len(events),
        "time_range": [start_time, end_time],
        "events": events,
        "note": "Only these records exist. Do not invent additional events." if events else "No matching records.",
    }


@function_tool()
async def correlate_events_tool(
    context: RunContext,
    alert_id: str,
) -> dict:
    """Build a time-ordered timeline from the retrieved records and list supporting, conflicting and missing evidence.

    Args:
        alert_id: The alert being investigated.
    """
    state = context.userdata
    denied = data_store.check_access(state, "correlate_events")
    if denied:
        return {"ok": False, "error": denied}

    if not state.active_alert or state.active_alert["alert_id"] != alert_id.strip().upper():
        return {"ok": False, "error": f"Load alert {alert_id} with get_alert_details first."}
    if not state.retrieved_events:
        return {"ok": False, "error": "No evidence has been retrieved yet. Run search_security_logs first."}

    try:
        state.correlation = data_store.correlate(state.active_alert, state.retrieved_events)
    except data_store.SisapError as exc:
        return {"ok": False, "error": str(exc)}

    return {"ok": True, **state.correlation}


@function_tool()
async def generate_investigation_report_tool(
    context: RunContext,
    alert_id: str,
    analyst_notes: str | None = None,
) -> dict:
    """Save a structured investigation report grounded in the retrieved evidence and correlation.

    Args:
        alert_id: The alert being investigated.
        analyst_notes: Optional extra notes from the conversation, in English.
    """
    state = context.userdata
    denied = data_store.check_access(state, "generate_investigation_report")
    if denied:
        return {"ok": False, "error": denied}

    if not state.active_alert or state.active_alert["alert_id"] != alert_id.strip().upper() or not state.correlation:
        return {
            "ok": False,
            "error": "A report needs the alert, retrieved logs and a correlation. "
                     "Run get_alert_details, search_security_logs and correlate_events first.",
        }

    try:
        report = data_store.create_report(
            alert=state.active_alert,
            events=state.retrieved_events,
            correlation_data=state.correlation,
            analyst_notes=analyst_notes,
        )
    except data_store.SisapError as exc:
        return {"ok": False, "error": str(exc)}

    state.last_report_id = report["report_id"]
    return {
        "ok": True,
        "report_id": report["report_id"],
        "review_status": report["review_status"],
        "recommended_next_checks": report["recommended_next_checks"],
        "uncertainties": report["uncertainties"],
    }


@function_tool()
async def hand_off_to_analyst_tool(
    context: RunContext,
    note: str | None = None,
    report_id: str | None = None,
    user_confirmed: bool = False,
) -> dict:
    """Hand the investigation report to a human SOC analyst for review. Requires explicit confirmation.

    Args:
        note: Optional handoff note in English.
        report_id: Report to hand off. Defaults to the latest report in this conversation.
        user_confirmed: True only after the analyst explicitly agreed.
    """
    state = context.userdata
    denied = data_store.check_access(state, "hand_off_to_analyst")
    if denied:
        return {"ok": False, "error": denied}

    rid = report_id or state.last_report_id
    if not rid:
        return {"ok": False, "error": "There is no report to hand off. Generate an investigation report first."}
    if not user_confirmed:
        return {
            "ok": False,
            "needs_confirmation": True,
            "instruction": f"Ask the analyst to confirm handing off {rid}, then call again with user_confirmed=true.",
        }

    try:
        r = data_store.hand_off_report(rid, note)
    except data_store.SisapError as exc:
        return {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "report_id": r["report_id"],
        "review_status": r["review_status"],
        "handoff": r["handoff"],
    }
