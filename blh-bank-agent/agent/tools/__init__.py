from .branch_tools import find_atm, find_branch, list_branches
from .calculator_tools import calculate_loan
from .escalation_tools import escalate_to_human
from .loan_tools import get_loan_info
from .otp_tools import send_otp, verify_otp
from .product_tools import get_product_info
from .faq_tools import search_faq

# List handed straight to the Agent's `tools=` argument.
ALL_TOOLS = [
    send_otp,
    verify_otp,
    get_product_info,
    get_loan_info,
    calculate_loan,
    find_branch,
    list_branches,
    find_atm,
    escalate_to_human,
    search_faq,
]
