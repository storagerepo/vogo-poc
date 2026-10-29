"""Knowledge retrieval tool — scoped to the categories the active workflow may read."""

from __future__ import annotations

from livekit.agents import function_tool, RunContext

from . import data_store


@function_tool()
async def search_knowledge_tool(
    context: RunContext,
    query: str,
    top_k: int = 3,
) -> dict:
    """Search the SISAP knowledge base (troubleshooting guides, playbooks, company info). Returns document sections with their source file.

    Args:
        query: English keywords describing what to look up, e.g. "VPN connection timed out UDP 4500".
        top_k: Number of document sections to return (1-5).
    """
    state = context.userdata
    denied = data_store.check_access(state, "search_knowledge")
    if denied:
        return {"ok": False, "error": denied}

    categories = data_store.WORKFLOW_KNOWLEDGE.get(state.workflow, {"company"})
    hits = data_store.search_knowledge(query, categories=categories, top_k=top_k)
    if not hits:
        return {"ok": True, "results": [], "message": "No relevant documentation found. Do not invent steps; offer to create a ticket or hand off."}
    return {"ok": True, "results": hits}
