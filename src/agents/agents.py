from langgraph.prebuilt import create_react_agent
from config import LLM
from src.tools.job_search_tools import search_jobs, score_resume
from src.tools.finance_tools import get_market_trend, get_stock_price, build_portfolio
from src.tools.news_tools import search_ai_news

# job search agent
job_serach_agent = create_react_agent(
    model = LLM,
    tools = [search_jobs, score_resume],
    name = "job_search_agent",
    prompt = "you are a job search assistant. Help iusers find relevant jobs based on their skills and preferences.  Use the search_jobs tool to find listings and score_resume to evaluate fit. Always present results clearly with company, title, and apply links "
)

# AI News Agent
ai_news_agent = create_react_agent(
    model=LLM,
    tools=[search_ai_news],
    name="ai_news_agent",
    prompt="You are an AI news assistant. Help users stay up to date with the latest developments in artificial intelligence. Search for relevant articles and provide concise summaries of the key points."
)

# Personal Finance Agent
finance_agent = create_react_agent(
    model=LLM,
    tools=[get_stock_price, get_market_trend, build_portfolio],
    name="finance_agent",
    prompt="You are a personal finance assistant. Help users analyze stocks, understand market trends, and build diversified portfolios based on their risk tolerance and investment goals. Always present data clearly and explain your reasoning."
)