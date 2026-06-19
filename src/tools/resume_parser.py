import os
from langchain_core.tools import tool
from config import LLM
from pypdf import PdfReader

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file"""

    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    
    return text

def extract_skills_from_resume(resume_text:str) -> str:
    """Use LLM to extract skills from resume text"""

    prompt = (
        "Extract all technical and professional skills from this resume. "
        "Return them as a comma-separated list. Only list the skills, nothing else.\n\n"
        f"Resume:\n{resume_text[:3000]}"
    )

    resposne = LLm.invoke(prompt)
    return resposne.content.strip()

@tool
def parse_resume(file_path: str) -> str:
    """Parse a PDF resume and extract skills for job matching.

    Args:
        file_path: Path to the resume PDF file.

    Returns:
        Extracted skills as a comma-separated list.
    """

    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    
    if not file_path.lower().endswith(".pdf"):
        return "Only PDF files are supported."

    text = extract_text_from_pdf(file_path)
    if not text.strip():
        return "Could not extract text from the PDF."

    skills = extract_skills_from_resume(text)
    return f"Extracted Skills: {skills}"