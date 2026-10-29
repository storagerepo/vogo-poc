from .routing import route_request_tool
from .knowledge import search_knowledge_tool
from .support import (
    record_troubleshooting_step_tool,
    run_diagnostic_tool,
    create_ticket_tool,
    get_ticket_status_tool,
    escalate_to_human_tool,
    confirm_resolution_tool,
)
from .soc import (
    get_alert_details_tool,
    search_security_logs_tool,
    correlate_events_tool,
    generate_investigation_report_tool,
    hand_off_to_analyst_tool,
)

ALL_TOOLS = [
    # Shared / Workflow routing & knowledge
    route_request_tool,
    search_knowledge_tool,
    # Technical Support workflow
    record_troubleshooting_step_tool,
    run_diagnostic_tool,
    create_ticket_tool,
    get_ticket_status_tool,
    escalate_to_human_tool,
    confirm_resolution_tool,
    # SOC Analyst Copilot workflow
    get_alert_details_tool,
    search_security_logs_tool,
    correlate_events_tool,
    generate_investigation_report_tool,
    hand_off_to_analyst_tool,
]

__all__ = [
    "ALL_TOOLS",
    "route_request_tool",
    "search_knowledge_tool",
    "record_troubleshooting_step_tool",
    "run_diagnostic_tool",
    "create_ticket_tool",
    "get_ticket_status_tool",
    "escalate_to_human_tool",
    "confirm_resolution_tool",
    "get_alert_details_tool",
    "search_security_logs_tool",
    "correlate_events_tool",
    "generate_investigation_report_tool",
    "hand_off_to_analyst_tool",
]
