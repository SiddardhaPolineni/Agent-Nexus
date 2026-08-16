import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_core.messages import HumanMessage
from src.guards.guardrails import run_guardrails
from src.agents.agents import job_search_agent, ai_news_agent, finance_agent
from src.prompts.agent_prompts import REASONING_PROMPT
from config import LLM

def call_api(prompt, options, context):
    """
    Red team provider - runs the full Agent Nexus flow:
    guardrails -> routing -> agent execution
    """

    if isinstance(prompt, list):
        query  = prompt[-1]["content"] if prompt else ""

    elif isinstance(prompt, str):
        try:
            import json
            parsed = json.loads(prompt)
            if isinstance(parsed, list):
                query = parsed[-1]["content"] if parsed else ""
            else:
                query = prompt
        except (json.JSONDecodeError, TypeError):
            query = prompt
    else:
        query = str(prompt)

    # Debug: write to file so we can see what's happening
    with open("eval/red_team/debug.txt", "a") as f:
        f.write(f"type={type(prompt).__name__} | repr={repr(prompt)[:300]}\n")
        f.write(f"query={repr(query)[:200]}\n---\n")

    print("query: ", query)

    if not query or not query.strip():
        return {"output": "No query provided"}

    # step 1: Guardrails

    guardrail_check = run_guardrails(query)

    if not guardrail_check["passed"]:
        return {"output": f"[BLOCKED] {guardrail_check['message']}"}

    # step - 2: Route
    routing_prompt = REASONING_PROMPT.format(query=query)
    response = LLM.invoke(routing_prompt)
    content = response.content.strip()

    print("content: ", content)
    intent = ""

    for line in content.split("\n"):
        if line.lower().startswith("intent:"):
            intent = line.split(":", 1)[1].strip().lower().strip("'\"")
    
    if not intent:
       intent = "general"

    # exeucte agents
    agents = {
        "job_search": job_search_agent,
        "ai_news": ai_news_agent,
        "finance": finance_agent
    }

    if intent == "general" or intent not in agents:
        general_response = LLM.invoke(query)
        return {"output": general_response.content}

    try:
        agent = agents[intent]
        result = agent.invoke({"messages": [HumanMessage(content=query)]})
        final_response = result["messages"][-1].content

        return {"output": final_response}

    except Exception as e:
        return {"output": f"Error: {str(e)}", "error": str(e)}


     