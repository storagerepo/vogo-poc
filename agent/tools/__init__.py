from .search_stays import search_stays_tool, get_stay_details_tool, check_availability_tool
from .booking import create_booking_tool, get_booking_status_tool, modify_or_cancel_booking_tool
from .issues import report_issue_tool, escalate_to_human_tool

ALL_TOOLS = [
    search_stays_tool,
    get_stay_details_tool,
    check_availability_tool,
    create_booking_tool,
    get_booking_status_tool,
    modify_or_cancel_booking_tool,
    report_issue_tool,
    escalate_to_human_tool,
]
