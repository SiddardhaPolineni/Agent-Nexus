from mcp.server.fastmcp import FastMCP 
from src.tools.job_search_tools import search_jobs, score_resume
from src.tools.news_tools import search_ai_news
from src.tools.finance_tools import get_stock_price, get_market_trend, build_portfolio

# create MCP server

mcp = FastMCP(
    name = "Agnet-Nexus",
    instructions = "Multi-agent system with job search, AI news and personal finance capabilities"
)

# job serach tools

@mcp.tool()
def nexus_search_jobs(query:str, location: str = "United States") -> str:
    """Search for relevant job listings based on role and location.
    
    Args:
        query: Job search query (e.g., 'Python developer', 'ML engineer')
        location: Geographic filter. Defaults to 'United States'
    """
    return search_jobs.invoke({"query": query, "location": location})


@mcp.tool()
def nexus_score_resume(job_title: str, skills: str)-> str:
    """Evaluate how well skills align with a target job role.
    
    Args:
        job_title: The job title to match against (e.g., 'Software Engineer')
        skills: Comma-separated list of skills (e.g., 'python, sql, react')
    """
    return score_resume.invoke({"job_title": job_title, "skills": skills})


# AI news tool
@mcp.tool()
def nexus_ai_news(query: str) -> str:
    """Search for the latest AI news and articles.
    
    Args:
        query: Topic to search (e.g., 'LLM breakthroughs', 'AI regulation')
    """
    return search_ai_news.invoke({"query": query})


# Finance tools
@mcp.tool()
def nexus_stock_price(ticker: str) -> str:
    """Get current stock price and key market data.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
    """
    return get_stock_price.invoke({"ticker": ticker})


@mcp.tool()
def nexus_market_trend(ticker: str, period: str = "1mo") -> str:
    """Get market trend data for a stock over a time period.
    
    Args:
        ticker: Stock ticker symbol
        period: Lookback period (1d, 5d, 1mo, 3mo, 6mo, 1y)
    """
    return get_market_trend.invoke({"ticker": ticker, "period": period})


@mcp.tool()
def nexus_build_portfolio(risk_level: str, investment_amount: float) -> str:
    """Build a diversified portfolio allocation.
    
    Args:
        risk_level: Risk tolerance - 'low', 'medium', or 'high'
        investment_amount: Total dollar amount to invest
    """
    return build_portfolio.invoke({"risk_level": risk_level, "investment_amount": investment_amount})


# Run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")