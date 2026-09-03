"""Tools that expose FAQ data for the BLH voice agent."""

from __future__ import annotations

from livekit.agents import function_tool

from .. import data_store


@function_tool()
async def search_faq(query: str) -> str:
    """Search the Frequently Asked Questions (FAQ) database for the user.

    Use this tool when a customer asks general questions about Internet Banking,
    Visa Debit cards, Credit Cards, limits, or general banking processes.

    Args:
        query: The search keywords (e.g. "Internet banking sign up", "card abroad", "maximum withdrawal")
    """
    results = data_store.find_faqs(query)
    
    if not results:
        # If specific query yields no results, maybe return top general ones or inform
        return "No specific FAQs found for that query. Suggest rephrasing or speaking to a representative."
        
    # Limit to top 3 to keep context concise
    top_results = results[:3]
    
    formatted = []
    for faq in top_results:
        formatted.append(f"Q: {faq['question']}\nA: {faq['answer']}")
        
    return "\n\n".join(formatted)
