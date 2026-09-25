from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def check_results_status(context: RunContext, patient_id: str, test_name: str) -> dict:
    """Check whether a lab-test result is ready for a given patient.
    Returns the status ('ready', 'processing', etc.) and, if ready,
    the date the result became available.

    Args:
        patient_id: The patient's ID, e.g. "P-1001".
        test_name: The test as the patient said it, e.g. "hemograma",
            "glucosa", "orina", "perfil lipídico".
    """
    result = data_store.get_result(patient_id, test_name)
    if not result:
        return {"found": False, "message": f"No result found for patient {patient_id} / test '{test_name}'."}
    return {"found": True, "result": result}


@function_tool()
async def explain_result(context: RunContext, patient_id: str, test_name: str) -> dict:
    """Retrieve a plain-language explanation of a patient's lab result.
    Only call this when the result status is 'ready'. Returns both the
    raw clinical summary and a patient-friendly explanation in Spanish
    and English.

    Args:
        patient_id: The patient's ID, e.g. "P-1001".
        test_name: The test as the patient said it, e.g. "hemograma".
    """
    result = data_store.get_result(patient_id, test_name)
    if not result:
        return {"found": False, "message": f"No result found for patient {patient_id} / test '{test_name}'."}
    if result.get("status") != "ready":
        return {"found": True, "ready": False, "status": result["status"],
                "message": "Result is not ready yet."}
    return {"found": True, "ready": True, "result": result}
