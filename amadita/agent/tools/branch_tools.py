from livekit.agents import RunContext, function_tool

from .. import data_store


@function_tool()
async def check_branch_capability(context: RunContext, branch_id: str, test_name: str) -> dict:
    """Confirm whether a specific branch currently performs a specific
    test (branches sometimes have a test temporarily unavailable, e.g.
    for equipment maintenance). Call this before assuming a patient's
    usual branch can run a newly requested test.

    Args:
        branch_id: Branch identifier, e.g. "naco", "piantini",
            "bella_vista", "santiago_agora", "la_vega". If you only have
            a branch's display name, use list_branches first to resolve it.
        test_name: The test to check, e.g. "perfil lipídico".
    """
    return data_store.branch_capability(branch_id, test_name)


@function_tool()
async def list_branches(context: RunContext) -> dict:
    """List all branches with their branch_id, display name, address,
    hours, and which tests they normally offer. Use this to resolve a
    branch name the patient mentioned into a branch_id, or to find
    nearby alternatives when a branch can't run a needed test.
    """
    return {"branches": data_store.branches}


@function_tool()
async def find_branches_offering_test(context: RunContext, test_name: str) -> dict:
    """Find every branch that currently offers a given test (accounting
    for any temporary unavailability). Use this when a patient's usual
    branch can't run a newly requested test and you need an alternative.

    Args:
        test_name: The test to search for, e.g. "perfil lipídico".
    """
    matches = data_store.branches_offering(test_name)
    return {"branches": matches}
