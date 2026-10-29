"""
data_store.py

A tiny in-memory / file-backed "database" over the mock JSON fixtures in
/mock_data. This stands in for SISAP's real backend & partner APIs during
the POC (see README for what gets swapped in later).

All functions here are plain Python — no LiveKit / Gemini imports — so
they can be unit tested independently of the voice stack.

Includes:
- Thread-safe JSON store (atomic writes + per-file locks)
- Domain errors (expected, user-facing failures)
- Workflow routing (deterministic, rules-based)
- Permissions (workflow-scoped tool access)
- Session state (per-session data kept in AgentSession.userdata)
- Service logic: tickets, diagnostics, security/alerts/correlation, reports, RAG, audit
- Guard decorator (permission check + error handling + audit for every tool handler)
"""

from __future__ import annotations

import copy
import functools
import json
import logging
import math
import os
import re
import threading
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Paths — point at /mock_data (Vogo convention)
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "mock_data"
KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge"

log = logging.getLogger("sisap.data_store")


# ===========================================================================
# 1. JSON STORE — thread-safe read / atomic write
# ===========================================================================

_GUARD = threading.Lock()
_LOCKS: dict[str, threading.RLock] = {}


def _lock_for(path: Path) -> threading.RLock:
    with _GUARD:
        return _LOCKS.setdefault(str(path), threading.RLock())


class JsonStore:
    """Read / atomically-update one JSON file.

    All JsonStore instances pointing at the same path share a lock, so concurrent
    voice sessions in the same worker process cannot corrupt the file.
    """

    def __init__(self, path: Path | str, default: Any = None):
        self.path = Path(path)
        self.default = default
        self._lock = _lock_for(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if default is not None and not self.path.exists():
            self._write(copy.deepcopy(default))

    def read(self) -> Any:
        with self._lock:
            if not self.path.exists():
                return copy.deepcopy(self.default)
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)

    def _write(self, data: Any) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)  # atomic on POSIX and Windows

    def update(self, fn: Callable[[Any], Any]) -> Any:
        """Run fn(data) under the lock (fn mutates data in place), then save."""
        with self._lock:
            data = self.read()
            result = fn(data)
            self._write(data)
            return result


# ===========================================================================
# 2. DOMAIN ERRORS — tool handlers convert these into safe, speakable messages
# ===========================================================================

class SisapError(Exception):
    """Base error for expected, user-facing failures."""


class NotFoundError(SisapError):
    pass


class ValidationError(SisapError):
    pass


class PermissionDeniedError(SisapError):
    pass


# ===========================================================================
# 3. SESSION STATE — per-session data kept in AgentSession.userdata
# ===========================================================================

SUPPORT = "support"
SOC = "soc"


@dataclass
class SessionState:
    session_id: str = "local"
    workflow: str | None = None
    user_name: str | None = None

    # ---- Technical Support task state ----
    device: str | None = None
    error_message: str | None = None
    steps_tried: list[str] = field(default_factory=list)
    diagnostics_run: list[dict[str, Any]] = field(default_factory=list)
    active_ticket_id: str | None = None
    resolved: bool | None = None

    # ---- SOC task state ----
    active_alert: dict[str, Any] | None = None
    retrieved_events: list[dict[str, Any]] = field(default_factory=list)
    correlation: dict[str, Any] | None = None
    last_report_id: str | None = None

    def reset_task(self) -> None:
        """Clear task-scoped data when the user switches workflow."""
        self.device = self.error_message = self.active_ticket_id = None
        self.steps_tried, self.diagnostics_run = [], []
        self.resolved = None
        self.active_alert = None
        self.retrieved_events, self.correlation = [], None
        self.last_report_id = None


# ===========================================================================
# 4. PERMISSIONS — workflow-scoped tool access
# ===========================================================================

SHARED_TOOLS = {"route_request", "search_knowledge"}

SUPPORT_TOOLS = {
    "record_troubleshooting_step",
    "run_diagnostic",
    "create_ticket",
    "get_ticket_status",
    "escalate_to_human",
    "confirm_resolution",
}

SOC_TOOLS = {
    "get_alert_details",
    "search_security_logs",
    "correlate_events",
    "generate_investigation_report",
    "hand_off_to_analyst",
}

WORKFLOW_TOOLS = {SUPPORT: SUPPORT_TOOLS, SOC: SOC_TOOLS}

# Knowledge categories each workflow may retrieve (see knowledge/manifest.json)
WORKFLOW_KNOWLEDGE = {
    SUPPORT: {"support", "company"},
    SOC: {"soc", "company"},
}


def check_access(state: SessionState, tool_name: str) -> str | None:
    """Return an error message if the tool is not allowed right now, else None."""
    if tool_name in SHARED_TOOLS:
        return None
    if state.workflow is None:
        return "No workflow selected yet. Call route_request first, or ask the user what they need."
    allowed = WORKFLOW_TOOLS.get(state.workflow, set())
    if tool_name not in allowed:
        return (
            f"Tool '{tool_name}' is not permitted in the '{state.workflow}' workflow. "
            "If the user really wants the other workflow, call route_request to switch."
        )
    return None


# ===========================================================================
# 5. ROUTING — deterministic intent classification (rules)
# ===========================================================================

CLARIFY = "clarify"

ALERT_RE = re.compile(r"\bALT-\d{3,}\b", re.I)
TICKET_RE = re.compile(r"\bTKT-\d{3,}\b", re.I)
USER_RE = re.compile(r"\buser\d{2,}\b|\b[a-z]+-svc-\d+\b", re.I)

STRONG_SUPPORT = {"vpn", "firewall", "dns", "ticket", "diagnostic", "connectivity", "wifi", "wi-fi", "router", "proxy", "ping"}
WEAK_SUPPORT = {"network", "internet", "connect", "connecting", "connection", "timeout", "timed", "latency", "slow", "error", "disconnects"}
STRONG_SOC = {"alert", "investigate", "investigation", "incident", "suspicious", "siem", "malware", "phishing", "compromised", "compromise", "powershell", "ioc", "brute"}
WEAK_SOC = {"security", "login", "logins", "logon", "authentication", "endpoint", "log", "logs", "failed", "attack"}
ACTION_WORDS = {"run", "check", "test", "execute", "perform"}
LOG_WORDS = {"login", "logins", "logon", "logs", "log", "failed", "authentication"}


@dataclass(frozen=True)
class RouteDecision:
    workflow: str  # "support" | "soc" | "clarify"
    first_tool: str | None
    reason: str
    missing_id: str | None = None  # e.g. "alert_id" when the workflow needs an ID


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9\-]+", text.lower()))


def classify_request(text: str) -> RouteDecision:
    tokens = _tokens(text)
    alert_id = ALERT_RE.search(text)
    ticket_id = TICKET_RE.search(text)

    support = 5 * bool(ticket_id) + 2 * len(tokens & STRONG_SUPPORT) + len(tokens & WEAK_SUPPORT)
    soc = 5 * bool(alert_id) + 2 * len(tokens & STRONG_SOC) + len(tokens & WEAK_SOC) + bool(USER_RE.search(text))

    if support == 0 and soc == 0:
        return RouteDecision(CLARIFY, None, "No recognizable support or security intent.")
    if abs(support - soc) < 2:
        return RouteDecision(CLARIFY, None, "Request could belong to both workflows.")

    if support > soc:
        if ticket_id:
            return RouteDecision(SUPPORT, "get_ticket_status", "Ticket ID mentioned.")
        if tokens & ACTION_WORDS and tokens & (STRONG_SUPPORT | {"network"}):
            return RouteDecision(SUPPORT, "run_diagnostic", "User asked to run a check.")
        return RouteDecision(SUPPORT, "search_knowledge", "Technical problem report.")

    if alert_id:
        return RouteDecision(SOC, "get_alert_details", "Alert ID mentioned.")
    if tokens & LOG_WORDS and USER_RE.search(text):
        return RouteDecision(SOC, "search_security_logs", "Log search for a named account.")
    return RouteDecision(SOC, "get_alert_details", "Security investigation without alert ID.", missing_id="alert_id")


# ===========================================================================
# 6. GUARD DECORATOR — permission check + error handling + audit
# ===========================================================================

def guarded(tool_name: str) -> Callable:
    def decorator(fn: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
        @functools.wraps(fn)
        def wrapper(state: SessionState, *args: Any, **kwargs: Any) -> dict[str, Any]:
            denied = check_access(state, tool_name)
            if denied:
                _audit_log(state.session_id, tool_name, "denied", {"reason": denied})
                return {"ok": False, "error": denied}
            try:
                result = fn(state, *args, **kwargs)
                _audit_log(state.session_id, tool_name, "ok" if result.get("ok", True) else "rejected",
                          {k: v for k, v in kwargs.items() if k != "agent_notes"})
                return result
            except SisapError as exc:  # expected failures: safe to speak aloud
                _audit_log(state.session_id, tool_name, "error", {"error": str(exc)})
                return {"ok": False, "error": str(exc)}
            except Exception:  # unexpected: do not leak internals to the user
                log.exception("Unexpected error in tool %s", tool_name)
                _audit_log(state.session_id, tool_name, "error", {"error": "internal"})
                return {"ok": False, "error": "Something went wrong while running that tool. Tell the user and offer to retry or escalate."}

        return wrapper

    return decorator


# ===========================================================================
# 7. SERVICE LAYER — all consolidated in one module (Vogo data_store pattern)
# ===========================================================================

# ---- Lazy-initialized service singletons ----

_tickets_store: JsonStore | None = None
_alerts_store: JsonStore | None = None
_auth_store: JsonStore | None = None
_endpoint_store: JsonStore | None = None
_users_store: JsonStore | None = None
_diagnostic_cfg: dict | None = None
_reports_store: JsonStore | None = None
_audit_store: JsonStore | None = None
_rag_chunks: list | None = None
_rag_df: Counter | None = None
_rag_avg_len: float = 1.0

# Test override support
_test_data_dir: Path | None = None
_test_knowledge_dir: Path | None = None


def _get_data_dir() -> Path:
    return _test_data_dir or DATA_DIR


def _get_knowledge_dir() -> Path:
    return _test_knowledge_dir or KNOWLEDGE_DIR


def set_test_dirs(data_dir: Path | None, knowledge_dir: Path | None = None) -> None:
    """Used by tests to point at a temporary copy of mock data."""
    global _test_data_dir, _test_knowledge_dir
    global _tickets_store, _alerts_store, _auth_store, _endpoint_store, _users_store
    global _diagnostic_cfg, _reports_store, _audit_store, _rag_chunks, _rag_df, _rag_avg_len
    _test_data_dir = data_dir
    _test_knowledge_dir = knowledge_dir
    # Reset all caches so they reload from the new dirs
    _tickets_store = _alerts_store = _auth_store = _endpoint_store = _users_store = None
    _diagnostic_cfg = None
    _reports_store = _audit_store = None
    _rag_chunks = None
    _rag_df = None
    _rag_avg_len = 1.0


def _tickets() -> JsonStore:
    global _tickets_store
    if _tickets_store is None:
        _tickets_store = JsonStore(_get_data_dir() / "tickets.json", default=[])
    return _tickets_store


def _alerts() -> JsonStore:
    global _alerts_store
    if _alerts_store is None:
        _alerts_store = JsonStore(_get_data_dir() / "alerts.json")
    return _alerts_store


def _auth() -> JsonStore:
    global _auth_store
    if _auth_store is None:
        _auth_store = JsonStore(_get_data_dir() / "auth_logs.json")
    return _auth_store


def _endpoint() -> JsonStore:
    global _endpoint_store
    if _endpoint_store is None:
        _endpoint_store = JsonStore(_get_data_dir() / "endpoint_events.json")
    return _endpoint_store


def _users() -> JsonStore:
    global _users_store
    if _users_store is None:
        _users_store = JsonStore(_get_data_dir() / "users.json")
    return _users_store


def _diag_cfg() -> dict:
    global _diagnostic_cfg
    if _diagnostic_cfg is None:
        _diagnostic_cfg = JsonStore(_get_data_dir() / "diagnostic_results.json").read()
    return _diagnostic_cfg


def _reports() -> JsonStore:
    global _reports_store
    if _reports_store is None:
        _reports_store = JsonStore(_get_data_dir() / "investigation_reports.json", default=[])
    return _reports_store


def _audit() -> JsonStore:
    global _audit_store
    if _audit_store is None:
        _audit_store = JsonStore(_get_data_dir() / "audit_logs.json", default=[])
    return _audit_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def _audit_log(session_id: str, tool: str, outcome: str, details: dict | None = None) -> None:
    entry = {
        "timestamp": _now(),
        "session_id": session_id,
        "tool": tool,
        "outcome": outcome,
        "details": details or {},
    }
    _audit().update(lambda data: data.append(entry))


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------

PRIORITIES = ("Low", "Medium", "High", "Critical")
STATUSES = ("Open", "In Progress", "Escalated", "Resolved", "Closed")
DEFAULT_TEAM = "SISAP Technical Support"
ESCALATION_TEAM = "SISAP Network Engineering (Tier 2)"


def get_ticket(ticket_id: str) -> dict:
    ticket_id = ticket_id.strip().upper()
    for t in _tickets().read():
        if t["ticket_id"] == ticket_id:
            return t
    raise NotFoundError(f"Ticket {ticket_id} does not exist.")


def create_ticket(issue: str, device: str | None, error: str | None, steps_tried: list[str],
                  priority: str = "Medium", requester: str | None = None,
                  diagnostics: list[dict] | None = None) -> dict:
    if not issue or not issue.strip():
        raise ValidationError("A ticket needs a description of the issue.")
    priority = priority.strip().capitalize() if priority else "Medium"
    if priority not in PRIORITIES:
        raise ValidationError(f"Priority must be one of {', '.join(PRIORITIES)}.")

    def _add(data: list) -> dict:
        nums = [int(t["ticket_id"].split("-")[1]) for t in data] or [0]
        ticket = {
            "ticket_id": f"TKT-{max(nums) + 1:03d}",
            "issue": issue.strip(),
            "device": device,
            "error": error,
            "steps_tried": list(steps_tried or []),
            "priority": priority,
            "status": "Open",
            "assigned_team": DEFAULT_TEAM,
            "requester": requester,
            "created_at": _now(),
            "diagnostics": diagnostics or [],
            "handoff": None,
        }
        data.append(ticket)
        return ticket

    return _tickets().update(_add)


def escalate_ticket(ticket_id: str, summary: str) -> dict:
    ticket_id = ticket_id.strip().upper()
    if not summary or not summary.strip():
        raise ValidationError("An escalation needs a short summary for the engineer.")

    def _esc(data: list) -> dict:
        for t in data:
            if t["ticket_id"] == ticket_id:
                t["status"] = "Escalated"
                t["assigned_team"] = ESCALATION_TEAM
                t["handoff"] = {
                    "summary": summary.strip(),
                    "escalated_at": _now(),
                    "to_team": ESCALATION_TEAM,
                    "steps_tried": t["steps_tried"],
                    "diagnostics": t["diagnostics"],
                }
                return t
        raise NotFoundError(f"Ticket {ticket_id} does not exist.")

    return _tickets().update(_esc)


def set_ticket_status(ticket_id: str, status: str) -> dict:
    ticket_id = ticket_id.strip().upper()
    if status not in STATUSES:
        raise ValidationError(f"Status must be one of {', '.join(STATUSES)}.")

    def _set(data: list) -> dict:
        for t in data:
            if t["ticket_id"] == ticket_id:
                t["status"] = status
                return t
        raise NotFoundError(f"Ticket {ticket_id} does not exist.")

    return _tickets().update(_set)


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def run_diagnostic(check_type: str, target: str) -> dict:
    cfg = _diag_cfg()
    check_type = (check_type or "").strip().lower()
    target = (target or "").strip().lower()
    if check_type not in cfg["check_types"]:
        raise ValidationError(f"Unknown check '{check_type}'. Allowed checks: {', '.join(cfg['check_types'])}.")
    host, _, port = target.partition(":")
    if check_type == "port_check" and not port.isdigit():
        raise ValidationError("A port_check target must look like host:port, e.g. vpn.mock-sisap.test:4500.")
    if host not in cfg["allowed_targets"]:
        raise PermissionDeniedError(
            f"Target '{host}' is not on the approved list. Approved targets: {', '.join(cfg['allowed_targets'])}."
        )
    key = f"{check_type}:{target}"
    result = cfg["results"].get(key, cfg["default_pass"])
    return {"check_type": check_type, "target": target, "simulated": True, **result}


# ---------------------------------------------------------------------------
# Security — alerts, log search, correlation
# ---------------------------------------------------------------------------

FAIL_TO_SUCCESS_MINUTES = 15
TRAVEL_MINUTES = 60
MAX_LOG_RESULTS = 50
LOG_WINDOW_MINUTES = 30


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def get_alert(alert_id: str) -> dict:
    alert_id = alert_id.strip().upper()
    for a in _alerts().read():
        if a["alert_id"] == alert_id:
            return a
    raise NotFoundError(f"Alert {alert_id} does not exist.")


def search_logs(username: str | None = None, source_ip: str | None = None,
                device: str | None = None, start: str | None = None, end: str | None = None,
                event_type: str | None = None) -> list[dict]:
    if not (username or source_ip or device):
        raise ValidationError("Provide at least a username, source IP or device to search logs.")
    start_dt = parse_ts(start) if start else None
    end_dt = parse_ts(end) if end else None

    def identity_match(e: dict) -> bool:
        return (
            bool(username and e.get("username") == username)
            or bool(source_ip and (e.get("source_ip") == source_ip or e.get("remote_ip") == source_ip))
            or bool(device and e.get("device") == device)
        )

    results = []
    for e in _auth().read():
        results.append({**e, "source": "auth", "description": e["event"]})
    for e in _endpoint().read():
        results.append({**e, "source": "endpoint", "description": e["activity"]})

    out = []
    for e in results:
        if not identity_match(e):
            continue
        ts = parse_ts(e["timestamp"])
        if start_dt and ts < start_dt:
            continue
        if end_dt and ts > end_dt:
            continue
        if event_type and event_type.lower() not in e["description"].lower():
            continue
        out.append(e)
    out.sort(key=lambda e: parse_ts(e["timestamp"]))
    return out[:MAX_LOG_RESULTS]


def _profile(username: str) -> dict:
    return next((u for u in _users().read() if u["username"] == username), {})


def correlate(alert: dict, events: list[dict]) -> dict:
    profile = _profile(alert["username"])
    known_ips = set(profile.get("known_ips", []))
    evs = sorted(events, key=lambda e: parse_ts(e["timestamp"]))

    timeline, prev = [], None
    for e in evs:
        notes = []
        if prev:
            mins = (parse_ts(e["timestamp"]) - parse_ts(prev["timestamp"])).total_seconds() / 60
            notes.append(f"{mins:.0f} min after {prev['event_id']}")
            if e.get("source_ip") and e.get("source_ip") == prev.get("source_ip"):
                notes.append("same source IP as previous event")
        timeline.append({
            "timestamp": e["timestamp"], "event_id": e["event_id"], "source": e["source"],
            "description": e["description"], "source_ip": e.get("source_ip") or e.get("remote_ip"),
            "device": e.get("device"), "country": e.get("country"), "notes": notes,
        })
        prev = e

    supporting, conflicting, missing = [], [], []
    auth = [e for e in evs if e["source"] == "auth"]
    successes = [e for e in auth if e["event"] == "Login Success"]
    failures = [e for e in auth if e["event"] == "Login Failed"]

    for s in successes:
        fails = [f for f in failures if f["source_ip"] == s["source_ip"]
                 and timedelta(0) <= parse_ts(s["timestamp"]) - parse_ts(f["timestamp"]) <= timedelta(minutes=FAIL_TO_SUCCESS_MINUTES)]
        if fails:
            supporting.append({
                "finding": f"{len(fails)} failed login(s) from {s['source_ip']} followed by a successful login ({s['event_id']}). "
                           "This pattern is worth investigating but does not prove compromise.",
                "evidence_ids": [f["event_id"] for f in fails] + [s["event_id"]],
            })

    seen_ips = set()
    for s in successes:
        ip = s["source_ip"]
        if ip in seen_ips:
            continue
        seen_ips.add(ip)
        ids = [x["event_id"] for x in successes if x["source_ip"] == ip]
        if ip in known_ips:
            conflicting.append({"finding": f"Successful login from {ip}, which is a known IP for {alert['username']}.", "evidence_ids": ids})
        elif known_ips:
            supporting.append({"finding": f"Successful login from {ip} ({s.get('country')}), which is not in the known IPs for {alert['username']}.", "evidence_ids": ids})

    for i, a in enumerate(successes):
        for b in successes[i + 1:]:
            gap = (parse_ts(b["timestamp"]) - parse_ts(a["timestamp"])).total_seconds() / 60
            if a.get("country") != b.get("country") and gap <= TRAVEL_MINUTES:
                supporting.append({
                    "finding": f"Successful logins from {a['country']} and {b['country']} only {gap:.0f} minutes apart (possible impossible travel; a VPN could also explain it).",
                    "evidence_ids": [a["event_id"], b["event_id"]],
                })

    for e in auth:
        if e["event"] == "Privileged Role Assigned":
            supporting.append({"finding": f"Privileged role assigned ({e['event_id']}) after the suspicious sign-in activity.", "evidence_ids": [e["event_id"]]})

    endpoint_evs = [e for e in evs if e["source"] == "endpoint"]
    susp = [e for e in endpoint_evs if e.get("risk") == "suspicious"]
    benign = [e for e in endpoint_evs if e.get("risk") == "benign"]
    if susp:
        supporting.append({"finding": f"{len(susp)} suspicious endpoint event(s) on {susp[0]['device']}: " + "; ".join(e["description"] for e in susp) + ".",
                           "evidence_ids": [e["event_id"] for e in susp]})
    for e in benign:
        conflicting.append({"finding": f"Benign activity on registered device {e['device']}: {e['description']} ({e['event_id']}).", "evidence_ids": [e["event_id"]]})

    for s in successes:
        if s.get("mfa_result") in (None, "Not Recorded"):
            missing.append({"finding": f"MFA result is not recorded for successful login {s['event_id']}.", "evidence_ids": [s["event_id"]]})
    if successes and not any(parse_ts(e["timestamp"]) > parse_ts(successes[0]["timestamp"]) for e in endpoint_evs):
        missing.append({"finding": "No endpoint telemetry after the first successful login, so post-login activity is unknown.", "evidence_ids": []})
    if not evs:
        missing.append({"finding": "No related log records were found for this alert.", "evidence_ids": []})

    return {
        "alert_id": alert["alert_id"],
        "event_count": len(evs),
        "timeline": timeline,
        "supporting_evidence": supporting,
        "conflicting_evidence": conflicting,
        "missing_evidence": missing,
        "disclaimer": "Correlation shows patterns in the retrieved records only. It does not by itself prove an account is compromised.",
    }


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

REVIEW_PENDING = "Pending Analyst Review"
REVIEW_HANDED_OFF = "Handed Off - Awaiting Analyst"

NEXT_CHECKS = [
    ("failed login", "Confirm with the account owner, through a verified channel, whether they attempted these logins."),
    ("not in the known", "Check the reputation and ownership of the new source IP and whether it is a corporate VPN or proxy."),
    ("impossible travel", "Check whether either source IP belongs to a corporate VPN, and review session tokens for both logins."),
    ("privileged role", "Review the privileged role change immediately and ask a human analyst to decide whether to revert it."),
    ("suspicious endpoint", "Collect endpoint forensic data (process tree, network connections) from the affected device."),
    ("mfa result", "Retrieve MFA provider logs to see whether MFA was challenged and who approved it."),
    ("no endpoint telemetry", "Pull endpoint telemetry after the login time to check post-login activity."),
]


def create_report(alert: dict, events: list[dict], correlation_data: dict, analyst_notes: str | None = None) -> dict:
    if not correlation_data or not correlation_data.get("timeline"):
        raise ValidationError("Cannot write a report without a correlated timeline built from retrieved records.")

    all_findings = [f["finding"].lower() for k in ("supporting_evidence", "conflicting_evidence", "missing_evidence") for f in correlation_data[k]]
    next_checks = [text for key, text in NEXT_CHECKS if any(key in f for f in all_findings)]
    next_checks.append("A human analyst decides on any containment (password reset, session revocation, device isolation). The copilot takes no response actions.")

    observed = [
        f"{t['timestamp']} - {t['event_id']}: {t['description']}"
        + (f" from {t['source_ip']}" if t.get("source_ip") else "")
        + (f" on {t['device']}" if t.get("device") else "")
        for t in correlation_data["timeline"]
    ]
    uncertainties = [correlation_data["disclaimer"]] + [f["finding"] for f in correlation_data["missing_evidence"]]

    def _add(data: list) -> dict:
        nums = [int(r["report_id"].split("-")[1]) for r in data] or [0]
        report = {
            "report_id": f"RPT-{max(nums) + 1:03d}",
            "alert_id": alert["alert_id"],
            "created_at": _now(),
            "alert_summary": {k: alert[k] for k in ("type", "severity", "username", "source_ip", "timestamp", "description")},
            "observed_facts": observed,
            "timeline": correlation_data["timeline"],
            "supporting_evidence": correlation_data["supporting_evidence"],
            "conflicting_evidence": correlation_data["conflicting_evidence"],
            "missing_evidence": correlation_data["missing_evidence"],
            "uncertainties": uncertainties,
            "recommended_next_checks": next_checks,
            "evidence_event_ids": [e["event_id"] for e in events],
            "agent_notes": analyst_notes,
            "review_status": REVIEW_PENDING,
            "handoff": None,
        }
        data.append(report)
        return report

    return _reports().update(_add)


def get_report(report_id: str) -> dict:
    for r in _reports().read():
        if r["report_id"] == report_id.strip().upper():
            return r
    raise NotFoundError(f"Report {report_id} does not exist.")


def hand_off_report(report_id: str, note: str | None) -> dict:
    report_id = report_id.strip().upper()

    def _h(data: list) -> dict:
        for r in data:
            if r["report_id"] == report_id:
                r["review_status"] = REVIEW_HANDED_OFF
                r["handoff"] = {"to": "SISAP SOC human analyst", "note": note, "handed_off_at": _now()}
                return r
        raise NotFoundError(f"Report {report_id} does not exist.")

    return _reports().update(_h)


# ---------------------------------------------------------------------------
# RAG — lightweight BM25 keyword retrieval over markdown guides
# ---------------------------------------------------------------------------

_RAG_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are", "it", "my", "i", "with",
    "how", "do", "does", "this", "that", "be", "can", "not", "no", "at", "by", "from", "as", "was", "has",
}


def _stem(tok: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if len(tok) > len(suf) + 3 and tok.endswith(suf):
            return tok[: -len(suf)]
    return tok


def _tokenize(text: str) -> list[str]:
    return [_stem(t) for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _RAG_STOPWORDS]


@dataclass
class _RagChunk:
    source: str
    doc_title: str
    category: str
    heading: str
    text: str
    tokens: list[str]


def _rag_sections(markdown: str) -> list[tuple[str, str]]:
    sections, heading, buf = [], "Overview", []
    for line in markdown.splitlines():
        if line.startswith("## "):
            sections.append((heading, "\n".join(buf)))
            heading, buf = line[3:].strip(), []
        elif line.startswith("# "):
            continue
        else:
            buf.append(line)
    sections.append((heading, "\n".join(buf)))
    return sections


def _load_rag():
    global _rag_chunks, _rag_df, _rag_avg_len
    knowledge_dir = _get_knowledge_dir()
    chunks: list[_RagChunk] = []
    df: Counter = Counter()

    manifest_path = knowledge_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    for path in sorted(knowledge_dir.glob("*.md")):
        meta = manifest.get(path.name, {})
        category = meta.get("category", "company")
        title = meta.get("title", path.stem.replace("_", " "))
        for heading, body in _rag_sections(path.read_text(encoding="utf-8")):
            text = body.strip()
            if not text:
                continue
            toks = _tokenize(f"{title} {heading} {text}")
            chunks.append(_RagChunk(path.name, title, category, heading, text, toks))
    for c in chunks:
        for t in set(c.tokens):
            df[t] += 1

    _rag_chunks = chunks
    _rag_df = df
    _rag_avg_len = (sum(len(c.tokens) for c in chunks) / len(chunks)) if chunks else 1.0


def search_knowledge(query: str, categories: set[str] | None = None, top_k: int = 3) -> list[dict]:
    global _rag_chunks
    if _rag_chunks is None:
        _load_rag()

    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    n = len(_rag_chunks)
    k1, b = 1.5, 0.75
    scored = []
    for c in _rag_chunks:
        if categories is not None and c.category not in categories:
            continue
        tf = Counter(c.tokens)
        score = 0.0
        for t in q_tokens:
            if t not in tf:
                continue
            idf = math.log(1 + (n - _rag_df[t] + 0.5) / (_rag_df[t] + 0.5))
            denom = tf[t] + k1 * (1 - b + b * len(c.tokens) / _rag_avg_len)
            score += idf * tf[t] * (k1 + 1) / denom
        if score > 0:
            scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "source": c.source,
            "document": c.doc_title,
            "section": c.heading,
            "content": c.text,
            "score": round(s, 2),
        }
        for s, c in scored[: max(1, min(top_k, 5))]
    ]
