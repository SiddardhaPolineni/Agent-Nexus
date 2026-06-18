from langgraph.graph import StateGraph, START, END 
from langgraph.checkpoint.memory import MemorySaver
from src.models.agent_state import AgentState
from src.agents.agents import job_serach_agent, finance_agent, ai_news_agent
from config import LLM

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
        return "ai_news"

    return {"next_agent": route, "current_agent": route}

def route_to_agent(state:AgentState)->AgentState:
    return state["next_agent"]

def build_graph():
    graph = StateGraph(AgentState)

    # Add nodes

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("job_search", job_serach_agent)
    graph.add_node("ai_news", ai_news_agent)
    graph.add_node("finance", finance_agent)

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
    graph.add_edge("job_search",END)
    graph.add_edge("ai_news", END)
    graph.add_edge("finance", END)

    memory = MemorySaver()

    graph_workflow = graph.compile(checkpointer=memory)

    return graph_workflow