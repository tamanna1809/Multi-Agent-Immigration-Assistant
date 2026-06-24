from langchain_core.tools import tool

@tool
def search_current_processing_times(query: str) -> str:
    """Search the web for current visa processing times and recent policy updates."""
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        tavily = TavilySearchResults(max_results=3)
        results = tavily.invoke(query)
        if isinstance(results, list):
            return "\n\n".join([r.get("content", "") for r in results[:3]])
        return str(results)
    except Exception as e:
        return f"Web search unavailable: {e}. Using knowledge base estimates only."
