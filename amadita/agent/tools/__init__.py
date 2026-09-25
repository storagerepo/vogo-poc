from .appointment_tools import book_appointment, check_appointment_slots
from .branch_tools import (
    check_branch_capability,
    find_branches_offering_test,
    list_branches,
)
from .escalation_tools import escalate_to_human
from .home_service_tools import (
    book_home_visit,
    check_home_service,
    list_home_service_branches,
)
from .notify_tools import send_confirmation
from .patient_tools import create_patient, get_patient_history, lookup_patient
from .results_tools import check_results_status, explain_result
from .test_tools import check_test_requirements

# One flat list, handed straight to the Agent's `tools=` argument.
ALL_TOOLS = [
    lookup_patient,
    get_patient_history,
    create_patient,
    check_test_requirements,
    check_branch_capability,
    list_branches,
    find_branches_offering_test,
    check_appointment_slots,
    book_appointment,
    check_results_status,
    explain_result,
    send_confirmation,
    escalate_to_human,
    check_home_service,
    list_home_service_branches,
    book_home_visit,
]
