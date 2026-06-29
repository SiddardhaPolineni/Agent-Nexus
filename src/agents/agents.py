from langgraph.prebuilt import create_react_agent
from config import LLM
from src.tools.job_search_tools import search_jobs, score_resume
from src.tools.tracker_tools import get_job_tracker, get_portfolio
from src.tools.finance_tools import get_market_trend, get_stock_price, build_portfolio
from src.tools.resume_parser import parse_resume
from src.tools.news_tools import search_ai_news
from src.prompts.agent_prompts import JOB_SEARCH_AGENT_PROMPT, AI_NEWS_AGENT_PROMPT, FINANCE_AGENT_PROMPT

# job search agent
job_search_agent = create_react_agent(
    model = LLM,
    tools = [search_jobs, score_resume, get_job_tracker, parse_resume],
    name = "job_search_agent",
    prompt = JOB_SEARCH_AGENT_PROMPT
)

# AI News Agent
ai_news_agent = create_react_agent(
    model=LLM,
    tools=[search_ai_news],
    name="ai_news_agent",
    prompt=AI_NEWS_AGENT_PROMPT
)

# Personal Finance Agent
finance_agent = create_react_agent(
    model=LLM,
    tools=[get_stock_price, get_market_trend, build_portfolio, get_portfolio],
    name="finance_agent",
    prompt=FINANCE_AGENT_PROMPT
)