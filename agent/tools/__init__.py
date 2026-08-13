from .search_stays import search_stays_tool, get_stay_details_tool, check_availability_tool
from .booking import create_booking_tool, get_booking_status_tool, modify_or_cancel_booking_tool
from .issues import report_issue_tool, escalate_to_human_tool
from .otp import send_otp_tool, verify_otp_tool
from .add_ons import get_available_add_ons_tool, validate_and_calculate_add_ons_tool, calculate_booking_total_tool

ALL_TOOLS = [
    search_stays_tool,
    get_stay_details_tool,
    check_availability_tool,
    create_booking_tool,
    get_booking_status_tool,
    modify_or_cancel_booking_tool,
    report_issue_tool,
    escalate_to_human_tool,
    send_otp_tool,
    verify_otp_tool,
    get_available_add_ons_tool,
    validate_and_calculate_add_ons_tool,
    calculate_booking_total_tool,
]
