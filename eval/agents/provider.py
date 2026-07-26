"""
Custom promptfoo provider that invokes Agent Nexus react agents.
Promptfoo calls the call_api function with the prompt (query) and returns the result.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_core.messages import HumanMessage
from src.agents.agents import job_search_agent, ai_news_agent, finance_agent

AGENTS = {
    "job_search": job_search_agent,
    "ai_news": ai_news_agent,
    "finance": finance_agent,
}


def call_api(prompt, options, context):
    """
    Promptfoo calls this function for each test case.
    The prompt contains the query. We use context vars to determine which agent to use.
    """
    agent_name = context.get("vars", {}).get("agent", "job_search")
    query = context.get("vars", {}).get("query", prompt)

    agent = AGENTS.get(agent_name)
    if not agent:
        return {"output": f"Error: Unknown agent '{agent_name}'"}

    try:
        result = agent.invoke({"messages": [HumanMessage(content=query)]})

        # Extract tools called
        tools_called = [
            msg.name for msg in result["messages"]
            if hasattr(msg, "name") and msg.name
        ]

        # Final response
        final_response = result["messages"][-1].content

        # Return structured output for assertions
        output = f"Tools: {', '.join(tools_called)}\n\nResponse:\n{final_response}"

        return {"output": output}

    except Exception as e:
        return {"output": f"Error: {str(e)}"}
