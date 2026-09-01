from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def check_test_requirements(context: RunContext, test_name: str) -> dict:
    """Look up prep rules for a lab test or imaging service: fasting hours,
    whether ID is required, duration (for imaging), and other prep notes.
    Always call this before booking or confirming a service so you can tell
    the patient how to prepare (e.g. "this needs 8 hours fasting",
    "no metallic objects for an MRI") instead of guessing.

    Args:
        test_name: The test or imaging service as the patient said it,
            e.g. "perfil lipídico", "hemograma", "resonancia",
            "CT scan", "sonografía", "rayos X".
    """
    service = data_store.get_service(test_name)
    if not service:
        return {"found": False, "message": f"No test or imaging service matched '{test_name}'."}
    return {"found": True, "test": service}
