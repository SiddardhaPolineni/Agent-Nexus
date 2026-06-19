from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt 
from langgraph.checkpoint.memory import MemorySaver
from src.models.agent_state import AgentState
from src.agents.agents import job_serach_agent, finance_agent, ai_news_agent
from src.tools.tracker_tools import save_portfolio, save_job_to_tracker
from src.guards.guardrails import run_guardrails
from src.prompts.agent_prompts import SUPERVISOR_PROMPT, GENERAL_PROMPT
from config import LLM

#==============================================
# Guardrail node: validates user input
#==============================================

def guardrail_node(state: AgentState) -> AgentState:
    """Check user input against guardrails before routing."""
    messages = state["messages"]
    user_message = messages[-1].content
    
    result = run_guardrails(user_message)
    
    if not result["passed"]:
        return {"next_agent": "blocked", "current_agent": "blocked", "messages": [("assistant", result["message"])]}
    
    return {"next_agent": "pass", "current_agent": "pass"}


def route_after_guardrail(state: AgentState) -> str:
    """Route based on guardrail result."""
    if state.get("next_agent") == "blocked":
        return "blocked"
    return "supervisor"


#==============================================
# Supervisor node: orchestrates the agent call.
#==============================================

def supervisor_node(state:AgentState) -> AgentState:
    """
        Route the user request to the appropriate agent
    """
    messages = state["messages"]
    
    # Use last 5 messages for context
    recent_messages = messages[-5:] if len(messages) > 5 else messages
    context = "\n".join([f"{'User' if msg.type == 'human' else 'Assistant'}: {msg.content[:200]}" for msg in recent_messages if hasattr(msg, 'content')])

    routing_prompt = SUPERVISOR_PROMPT.format(context=context)

    response = LLM.invoke(routing_prompt)

    route = response.content.strip().lower()

    # Default fallback
    if route not in ["job_search", "ai_news", "finance", "general"]:
        route = "general"

    return {"next_agent": route, "current_agent": route}

#=========================================================
# route to the dedicated agent based on the query intent.
#=========================================================

def route_to_agent(state:AgentState)->AgentState:
    return state["next_agent"]

#=========================================================
# General node: handles greetings and casual conversation
#=========================================================

def general_node(state: AgentState) -> AgentState:
    """Handle greetings and general queries directly without tools."""
    messages = state["messages"]
    
    # Use last 5 messages for conversational context
    recent_messages = messages[-5:] if len(messages) > 5 else messages
    context = "\n".join([f"{'User' if msg.type == 'human' else 'Assistant'}: {msg.content[:200]}" for msg in recent_messages if hasattr(msg, 'content')])

    response = LLM.invoke(GENERAL_PROMPT.format(context=context))

    return {"messages": [("assistant", response.content)]}

#==================================================================
# Job review node to get the feeback from the human on job results.
#==================================================================

def job_review_node(state:AgentState)->AgentState:
    """Pause for user to review job results before marking as applied."""
    last_message = state["messages"][-1].content

    feedback = interrupt(
        {
            "messages": "Here are the job results. Would you like to mark any as applied?",
            "agent_output": last_message,
            "action_required": "Reply 'yes' to confirm or provide feedback"
        }
    )

    return {"human_feedback": feedback, "approved": feedback.strip().lower()}

#===============================================================================
# Finance review node to get the feedback from the human of suggested portfolio
#===============================================================================

def finance_review_node(state:AgentState) -> AgentState:
    """Pause for user to approve the suggested portfolio."""
    last_message = state["messages"][-1].content

    feedback = interrupt(
        {
            "messages": "Here is your suggested portfolio. Do you approve this allocation?",
            "agent_output": last_message,
            "action_required": "Reply 'yes' to finalize or provide changes"
        }
    )

    return  {"human_feedback": feedback, "approved": feedback.strip().lower()}

#======================================================================
#       Finalize job application and update the job tracker.
#======================================================================

def job_finalize_node(state: AgentState) -> AgentState:
    """Finalize job application tracking based on user approval."""
    approved = state.get("approved", "")
    feedback = state.get("human_feedback", "")
    
    if approved == "yes":
        # Extract job info from the agent's last response
        messages = state.get("messages", [])
        job_details = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.type == "ai" and ("company" in msg.content.lower() or "job" in msg.content.lower()):
                job_details = msg.content
                break
        
        # Parse jobs from the response and save them
        import re
        lines = job_details.split("\n")
        saved_count = 0
        
        current_title = ""
        current_company = ""
        current_location = ""
        current_link = ""
        
        for line in lines:
            line = line.strip()
            # Match numbered job listings
            title_match = re.match(r'^\d+\.\s*(.+)', line)
            if title_match:
                # Save previous job if exists
                if current_title and current_company:
                    save_job_to_tracker.invoke({
                        "job_title": current_title,
                        "company": current_company,
                        "location": current_location or "N/A",
                        "link": current_link or "N/A",
                        "status": "Applied"
                    })
                    saved_count += 1
                current_title = title_match.group(1).strip()
                current_company = ""
                current_location = ""
                current_link = ""
            elif "company" in line.lower():
                current_company = line.split(":", 1)[-1].strip() if ":" in line else line
            elif "location" in line.lower():
                current_location = line.split(":", 1)[-1].strip() if ":" in line else line
            elif "link" in line.lower() or "http" in line.lower():
                urls = re.findall(r'https?://\S+', line)
                current_link = urls[0] if urls else line.split(":", 1)[-1].strip() if ":" in line else ""
        
        # Save the last job
        if current_title and current_company:
            save_job_to_tracker.invoke({
                "job_title": current_title,
                "company": current_company,
                "location": current_location or "N/A",
                "link": current_link or "N/A",
                "status": "Applied"
            })
            saved_count += 1
        
        return {"messages": [("assistant", f"{saved_count} job(s) marked as applied and saved to your tracker!")]}
    elif approved == "no":
        return {"messages": [("assistant", "No jobs marked as applied. Let me know if you'd like to search again.")]}
    else:
        # User gave specific feedback — use LLM to respond intelligently
        messages = state.get("messages", [])
        job_details = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.type == "ai" and ("company" in msg.content.lower() or "job" in msg.content.lower()):
                job_details = msg.content
                break
        
        response = LLM.invoke(
            f"You are a job search assistant. The user was shown these job results:\n\n"
            f"{job_details[:1000]}\n\n"
            f"The user provided this feedback: '{feedback}'\n\n"
            f"Respond helpfully based on their feedback. If they want to refine the search, suggest what to do next. "
            f"If they want specific jobs saved, confirm which ones."
        )
        return {"messages": [("assistant", response.content)]}


#===========================================================
#   Finalize the suggest portfolio if user says yes
#===========================================================

def finance_finalize_node(state: AgentState) -> AgentState:
    """Finalize portfolio based on user approval."""
    approved = state.get("approved", "")
    feedback = state.get("human_feedback", "")
    
    if approved == "yes":
        # Extract portfolio info from the last agent message and save it
        messages = state.get("messages", [])
        portfolio_details = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.type == "ai" and "portfolio" in msg.content.lower():
                portfolio_details = msg.content
                break
        
        # Parse basic info from the agent's response
        risk_level = "medium"
        investment_amount = 0.0
        import re
        for line in portfolio_details.lower().split("\n"):
            if "risk" in line and "high" in line:
                risk_level = "high"
            elif "risk" in line and "low" in line:
                risk_level = "low"
            if "$" in line and ("amount" in line or "invest" in line):
                amounts = re.findall(r'\$[\d,]+\.?\d*', line)
                if amounts:
                    investment_amount = float(amounts[0].replace("$", "").replace(",", ""))
        
        # Save to CSV
        save_portfolio.invoke({
            "risk_level": risk_level,
            "investment_amount": investment_amount,
            "allocations": portfolio_details[:500]
        })
        
        return {"messages": [("assistant", "Portfolio finalized and saved to your tracker!")]}
    elif approved == "no":
        return {"messages": [("assistant", "Portfolio discarded. Let me know if you'd like to try a different allocation.")]}
    else:
        # User gave specific feedback — use LLM to respond intelligently
        messages = state.get("messages", [])
        portfolio_details = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.type == "ai" and "portfolio" in msg.content.lower():
                portfolio_details = msg.content
                break
        
        response = LLM.invoke(
            f"You are a personal finance assistant. The user was shown this portfolio suggestion:\n\n"
            f"{portfolio_details[:1000]}\n\n"
            f"The user provided this feedback: '{feedback}'\n\n"
            f"Respond helpfully. If they want changes to the allocation, suggest an updated portfolio. "
            f"If they want more info on a specific asset, provide it."
        )
        return {"messages": [("assistant", response.content)]}


#=======================
#   Build Graph
#=======================

def build_graph():
    graph = StateGraph(AgentState)

    # Add nodes

    graph.add_node("guardrail", guardrail_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("general", general_node)
    graph.add_node("job_search", job_serach_agent)
    graph.add_node("ai_news", ai_news_agent)
    graph.add_node("finance", finance_agent)
    graph.add_node("job_review", job_review_node)
    graph.add_node("finance_review", finance_review_node)
    graph.add_node("job_finalize", job_finalize_node)
    graph.add_node("finance_finalize", finance_finalize_node)

    # Add Edges

    graph.add_edge(START, "guardrail")
    graph.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {
            "blocked": END,
            "supervisor": "supervisor"
        }
    )
    graph.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "job_search": "job_search",
            "ai_news": "ai_news",
            "finance": "finance",
            "general": "general"
        }
    )
    graph.add_edge("general", END)
    graph.add_edge("job_search","job_review")
    graph.add_edge("job_review", "job_finalize")
    graph.add_edge("job_finalize", END)

    graph.add_edge("ai_news", END)

    graph.add_edge("finance", "finance_review")
    graph.add_edge("finance_review", "finance_finalize")
    graph.add_edge("finance_finalize", END)
    

    memory = MemorySaver()

    graph_workflow = graph.compile(checkpointer=memory)

    return graph_workflow