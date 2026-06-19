from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt 
from langgraph.checkpoint.memory import MemorySaver
from src.models.agent_state import AgentState
from src.agents.agents import job_serach_agent, finance_agent, ai_news_agent
from config import LLM

#==============================================
# Supervisor node: orchestrates the agent call.
#==============================================

def supervisor_node(state:AgentState) -> AgentState:
    """
        Route the user request to the appropriate agent
    """
    messages = state["messages"]

    routing_prompt = (
        "You are a routing supervisor. Based on the user's message, decide which agent should handle it.\n"
        "Respond with ONLY one of these exact words:\n"
        "- 'job_search' — for job hunting, resume, career-related queries\n"
        "- 'ai_news' — for AI news, tech updates, articles\n"
        "- 'finance' — for stocks, portfolio, market trends, investing\n\n"
        f"User message: {messages[-1].content}"
    )

    response = LLM.invoke(routing_prompt)

    route = response.content.strip().lower()

    print(route)

    # Default fallback
    if route not in ["job_search", "ai_news", "finance"]:
        route = "ai_news"

    return {"next_agent": route, "current_agent": route}

#=========================================================
# route to the dedicated agent based on the query intent.
#=========================================================

def route_to_agent(state:AgentState)->AgentState:
    return state["next_agent"]

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

    return {"human_feedback": feedback, "approved": feedback.lower()}

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

    return  {"human_feedback": feedback, "approved": feedback.lower()}

#======================================================================
#       Finalize job application and update the job tracker.
#======================================================================

def job_finalize_node(state: AgentState) -> AgentState:
    """Finalize job application tracking based on user approval."""
    if state.get("approved"):
        return {"messages": [("assistant", "Jobs marked as applied in your tracker. Good luck!")]}
    else:
        feedback = state.get("human_feedback", "")
        return {"messages": [("assistant", f"Got it. No jobs marked. Your feedback: {feedback}")]}


#===========================================================
#   Finalize the suggest portfolio if user says yes
#===========================================================

def finance_finalize_node(state: AgentState) -> AgentState:
    """Finalize portfolio based on user approval."""
    if state.get("approved"):
        return {"messages": [("assistant", "Portfolio finalized! Your allocation has been saved.")]}
    else:
        feedback = state.get("human_feedback", "")
        return {"messages": [("assistant", f"Portfolio not finalized. Your feedback: {feedback}")]}


#=======================
#   Build Graph
#=======================

def build_graph():
    graph = StateGraph(AgentState)

    # Add nodes

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("job_search", job_serach_agent)
    graph.add_node("ai_news", ai_news_agent)
    graph.add_node("finance", finance_agent)
    graph.add_node("job_review", job_review_node)
    graph.add_node("finance_review", finance_review_node)
    graph.add_node("job_finalize", job_finalize_node)
    graph.add_node("finance_finalize", finance_finalize_node)

    # Add Edges

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "job_search": "job_search",
            "ai_news": "ai_news",
            "finance": "finance"
        }
    )
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