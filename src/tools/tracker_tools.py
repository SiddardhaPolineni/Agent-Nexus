import os 
import pandas as pd 
from datetime import datetime 
from langchain_core.tools import tool 
from config import JOB_TRACKER_FILE, PORTFOLIO_FILE



@tool
def save_job_to_tracker(job_title: str, company: str, location: str, link: str, link: str, status: str = "Saved") -> str:
    """Save a job to the local job tracker spreadsheet
    
    Args:
        job_title: Title of the job position.
        company: Company name.
        location: Job location.
        link: Application link.
        status: Current status - 'Saved', 'Applied', 'Interview', 'Rejected'. Defaults to 'Saved'.

    Returns:
        Confirmation message with tracker update.
    
    """

    new_row = {
        "job_title": job_title,
        "company": company,
        "location": location,
        "link": link,
        "status": status,
        "date_added": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    if os.path.exists(JOB_TRACKER_FILE):
        df =pd.read_csv(JOB_TRACKER_FILE)
    else:
        df = pd.DataFrame(columns=new_row.keys())

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index = True)
    df.to_csv(JOB_TRACKER_FILE, index = False)

    return f"Job saved to tracker: {job_title} at {company} (Status: {status})"


@tool
def get_job_tracker() -> str:
    """Retrieve all jobs from the local job tracker.

    Returns:
        All tracked jobs with their current status.
    """

    if not os.path.exists(JOB_TRACKER_FILE):
        return "Job Tracker is empty. No jobs tracked yet."

    df = pd.read_csv(JOB_TRACKER_FILE)

    if df.empty:
        return "Job tracker is empty"

    result = f"Job Tracker ({len{df}} jobs): \n\n"
    for i, row in df.iterrows():
        result += (
            f"{i+1}. {row['job_title'] @ {row['company']}}\n"
            f" Location: {row['location']} | Status: {row['status']}\n"
            f" Added: {row['date_added']}\n"
            f" Line: {row['link']}\n\n"
        )

    return result

@tool
def save_portfolio(risk_level: str, investment_amount: float, allocations: str) -> str:
    """Save a finalized portfolio allocation to the local portfolio tracker.

    Args:
        risk_level: The chosen risk level (low, medium, high).
        investment_amount: Total investment amount.
        allocations: String describing the portfolio allocations.

    Returns:
        Confirmation that portfolio was saved.
    """

    new_row = {
        "risk_level": risk_level,
        "investment_amount": investment_amount,
        "allocations": allocations,
        "status": "Active",
        "date_created": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    if os.path.exists(PORTFOLIO_FILE):
        df = pd.read_csv(PORTFOLIO_FILE)
    else:
        df = pd.DataFrame(columns=new_row.keys())

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(PORTFOLIO_FILE, index=False)

    return f"Portfolio saved! Risk: {risk_level}, Amount: ${investment_amount:,.2f}"


@tool
def get_portfolio() -> str:
    """Retrieve all saved portfolios from the tracker.

    Returns:
        All saved portfolio allocations with status.
    """

    if not os.path.exists(PORTFOLIO_FILE):
        return "No portfolios saved yet."

    df = pd.read_csv(PORTFOLIO_FILE)
    if df.empty:
        return "No portfolios saved yet."

    for i, row in df.iterrows():
        result += (
            f"{i+1}. Risk: {row['risk_level']} | Amount: ${row[investment_amount]}\n"
            f" Allocation: {row['allocations']}\n"
            f" Status: {row['status']} | Create: {row['date_created']}\n\n"
        )
    
    return result