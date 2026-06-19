from config import LLM
from src.prompts.agent_prompts import GUARDRAIL_PROMPT

# ===== Input Validation =====

def validate_input(message: str) -> dict:
    """Basic input validation checks.
    
    Returns:
        dict with 'valid' (bool) and 'reason' (str if invalid)
    """
    # Empty check
    if not message or not message.strip():
        return {"valid": False, "reason": "Please enter a message."}
    
    # Length check
    if len(message) > 2000:
        return {"valid": False, "reason": "Message too long. Please keep it under 2000 characters."}
    
    return {"valid": True, "reason": ""}


# ===== Topic Guardrail =====

def check_topic_allowed(message: str) -> dict:
    """Use LLM to check if the message is within allowed topics.
    
    Allowed: job search, AI/tech news, personal finance, general greetings.
    Blocked: harmful content, unrelated topics (cooking, medical advice, etc.)
    
    Returns:
        dict with 'allowed' (bool) and 'reason' (str if blocked)
    """
    response = LLM.invoke(GUARDRAIL_PROMPT.format(message=message))
    
    result = response.content.strip()
    
    if result.upper().startswith("ALLOWED"):
        return {"allowed": True, "reason": ""}
    else:
        reason = result.replace("BLOCKED:", "").replace("BLOCKED", "").strip()
        if not reason:
            reason = "This topic is outside my expertise. I can help with job searching, AI news, and personal finance."
        return {"allowed": False, "reason": reason}


# ===== Prompt Injection Detection =====

def detect_injection(message: str) -> dict:
    """Check for common prompt injection patterns.
    
    Returns:
        dict with 'safe' (bool) and 'reason' (str if unsafe)
    """
    injection_patterns = [
        "ignore previous instructions",
        "ignore all instructions",
        "disregard your instructions",
        "forget your rules",
        "you are now",
        "act as",
        "pretend you are",
        "system prompt",
        "reveal your instructions",
        "what are your instructions",
        "override your",
        "jailbreak",
        "DAN mode",
    ]
    
    message_lower = message.lower()
    for pattern in injection_patterns:
        if pattern in message_lower:
            return {"safe": False, "reason": "I can't process that request. How can I help you with jobs, AI news, or finance?"}
    
    return {"safe": True, "reason": ""}


# ===== Main Guardrail Check =====

def run_guardrails(message: str) -> dict:
    """Run all guardrail checks on user input.
    
    Returns:
        dict with 'passed' (bool) and 'message' (str - error message if failed)
    """
    # 1. Input validation
    validation = validate_input(message)
    if not validation["valid"]:
        return {"passed": False, "message": validation["reason"]}
    
    # 2. Prompt injection check (fast, no LLM call)
    injection = detect_injection(message)
    if not injection["safe"]:
        return {"passed": False, "message": injection["reason"]}
    
    # 3. Topic check (uses LLM)
    topic = check_topic_allowed(message)
    if not topic["allowed"]:
        return {"passed": False, "message": topic["reason"]}
    
    return {"passed": True, "message": ""}
