from langchain.tools import tool
import requests
from config import RAPID_API_KEY, RAPID_JSEARCH_URL, RAPID_API_HOST

# ======================================
# Tool definitions
# ======================================

@tool
def search_jobs(query:str, location:str = "United States") -> str:
    """Search for relevant job listings using the JSearch API.

    Args:
        query: Job search query describing the desired role (e.g., 'Python developer', 'ML engineer').
        location: Geographic filter for the job search. Defaults to 'United States'.

    Returns:
        Top 5 matching job listings with title, company, location, and application link.
    """
    print(f"API Key loaded: {RAPID_API_KEY is not None}")
    print(f"URL: {RAPID_JSEARCH_URL}")

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": RAPID_API_HOST
    }

    params = {"query": f"{query} in {location}","num_pages":1}
    response = requests.get(RAPID_JSEARCH_URL,headers=headers,params=params)
    print(response)
    if response.status_code != 200:
        return f"Error fetching the jobs"
    
    jobs = response.json().get("data", [])[:5]

    if not jobs:
        return "No jobs found for this query"

    result = ""

    for i,job in enumerate(jobs,1):
        result +=(
            f"{i}. {job.get('job_title', 'N/A')}\n"
            f" Company: {job.get('employer_name','N/A')}\n"
            f" Location: {job.get('job_city', '')}, {job.get('job_country', '')}\n"
            f" Link: {job.get('job_apply_link', 'N/A')}\n\n"
        )

    return result

@tool
def score_resume(job_title:str, skills:str) -> str:
    """Evaluate how well a user's skills align with a target job role.

    Args:
        job_title: The job title to match against (e.g., 'Software Engineer', 'Data Scientist').
        skills: Comma-separated list of the user's skills (e.g., 'python, sql, machine learning').

    Returns:
        A match score percentage along with matched and missing skills breakdown.
    """


    skills_list = [s.strip().lower() for s in skills.strip(",")]

    common_requirements = {
        "software engineer": ["python", "java", "sql", "git", "algorithms"],
        "data scientist": ["python", "machine learning", "sql", "statistics", "pandas"],
        "frontend developer": ["javascript", "react", "css", "html", "typescript"],
        "ai engineer": ["python", "LangChain", "LangGraph", "FastAPI", "RAG", "AI Agents"],
        "data engineer": ["sql", "spark", "python", "data modeling", "data warehousing"]
    }

    reqs = common_requirements.get(job_title.lower(), ["python", "communication", "problem solving"])
    matches = [s for s in skills_list if s in reqs]
    score = len(matches) / len(reqs) * 100

    return f"Resume Score for '{job_title}': {score:.0f}%\nMatched: {', '.join(matches)}\nMissing: {', '.join(set(reqs) - set(matches))}"
