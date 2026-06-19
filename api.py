from fastapi import FastAPI 
from pydantic import BaseModel
from src.graph.graph import build_graph
from langgraph.types import Command
from fastapi.responses import StreamingResponse
import json

app = FastAPI(title="Agent Nexus")

graph = build_graph()

sessions = {}

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ResumeRequest(BaseModel):
    thread_id: str
    feedback: str

@app.post("/chat")
async def chat(request: ChatRequest):
    """Send a message and get the full response"""

    config = {"configurable": {"thread_id": request.thread_id}}

    response = graph.invoke(
        {"messages": [("user", request.message)]},
        config = config
    )

    state = graph.get_state(config)

    waiting_for_input = bool(state.next)

    return {
        "response": response["messages"][-1].content,
        "thread_id": request.thread_id,
        "waiting_for_input": waiting_for_input,
        "interrupted_at": state.next[0] if waiting_for_input else None
    }

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream agent responses as Server-Sent Events"""

    config = {"configurable": {"thread_id": request.thread_id}}

    def event_stream():

        for event in graph.stream(
            {
                "messages": [("user",request.message)]
            },
            config = config,
            stream_mode ="updates"
        ):
            for node_name, node_output in event.items():
                #stream each nodes output as it completes
                data = {
                    "node": node_name,
                    "content": ""
                }

                if "messages" in node_output:

                    messages = node_output["messages"]

                    if messages:
                        last_msg = messages[-1]
                        #handle both AI messages and tuples
                        if hasattr(last_msg, "content"):
                            data["content"] = last_msg.content
                        elif isinstance(last_msg, tuple):
                            data["content"] = last_msg[1]
            
            yield f"data: {json.dumps(data)}\n\n"
        
        state= graph.get_state(config)
        if state.next:
            yield f"data: {json.dumps({'node': 'interrupt', 'content': 'Waiting for your input...', 'waiting_for_input': True})}\n\n"
                           
        yield f"data: {json.dumps({'node': 'done', 'content': ''})}\n\n"
    
    return StreamingResponse(event_stream(), media_type = "text/event-stream")


@app.post("/resume")
async def resume(request: ResumeRequest):
    """Resume a paused graph with human feedback."""

    config = {"configurable": {"thread_id":request.thread_id}}

    state = graph.get_state(config)

    if not state.next:
        return {"error": "no pending interrupt for this session."}

    response = graph.invoke(
        Command(resume = request.feedback),
        config = config
    )

    return {
        "response": response["messages"][-1].content,
        "thread_id": request.thread_id,
        "approved": request.feedback.lower().strip() == "yes"
    }

@app.post("resume/stream")
async def resume_stream(request: ResumeRequest):
    """Resume with streaming output"""

    config = {"configurable":{"thread_id":request.thread_id}}

    state = graph.get_state(config)

    if not state.next:
        return {"error": "No pending interrupt of this session."}

    def event_stream():
        for event in graph.stream(
            Command(resume=request.feedback),
            config = config,
            stream_mode = "updates"
        ):
            for node_name, node_output in event.items():
                data = {"node": node_name, "content": ""}
                if "messages" in node_output:
                    messages = node_output["messages"]
                    if messages and hasattr(messages[-1], "content"):
                        data["content"] = messages[-1].content

                yield f"data: {json.dumps(data)}\n\n"
        
        yield f"data: {json.dumps({'node': 'done', 'content': ''})}\n\n"
    
    return StreamingResponse(event_stream(), media_type = "text/event-stream")

@app.get("/history/{thread_id}")
async def get_history(thread_id: str):
    """Get conversation history for a thread."""
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)

    if not state.values.get("messages"):
        return {"messages": []}

    messages = [
        {"role": msg.type, "content": msg.content}
        for msg in state.values["messages"]
    ]
    return {"messages": messages}


@app.get("/health")
async def health():
    return {"status": "running", "agents": ["job_search", "ai_news", "finance"]}