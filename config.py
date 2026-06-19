from dotenv import load_dotenv
import os
from langchain_openai import OpenAI, ChatOpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
RAPID_JSEARCH_URL = os.getenv("RAPID_JSEARCH_URL")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
RAPID_API_HOST = os.getenv("RAPID_API_HOST")

# file paths 
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
JOB_TRACKER_FILE = os.path.join(DATA_DIR, "job_tracker.csv")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.csv")

LLM = ChatOpenAI(model = "gpt-4o", temperature = 0)



