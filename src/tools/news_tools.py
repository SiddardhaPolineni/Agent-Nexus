# from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from config import TAVILY_API_KEY

search_tool = TavilySearch(max_results = 5, tavily_api_key = TAVILY_API_KEY)

@tool
def search_ai_news(quesry:str) -> str:
    """Search the web for the latest AI news and articles.

    Args:
        query: Topic or keyword to search for (e.g., 'LLM breakthroughs', 'OpenAI updates', 'AI regulation').

    Returns:
        Top 5 recent articles with title, URL, and a brief summary of each.
    """


    results = search_tool.invoke(query)

    if not results:
        return "No news articles found."

    output = ""

    for i, result in enumerate(results, 1):
        output += (
            f"{i}. {result.get('title', 'N/A')}\n"
            f" URL: {result.get('url', 'N/A')}\n"
            f" Summary: {result.get('content', 'N/A')[:200]}\n\n"
        )
    
    return output