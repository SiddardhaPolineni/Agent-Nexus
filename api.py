from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.graph.graph import build_graph
from langgraph.types import Command
from fastapi.responses import StreamingResponse
import json

app = FastAPI(title="Agent Nexus", version="1.0.0")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ResumeRequest(BaseModel):
    thread_id: str
    feedback: str


# --- Root endpoint ---
@app.get("/")
async def root():
    return {
        "app": "Agent Nexus",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat/stream": "Stream agent response via SSE",
            "POST /resume/stream": "Resume paused graph with streaming output",
            "GET /history/{thread_id}": "Get conversation history",
            "GET /health": "Health check"
        }
    }


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream agent responses as Server-Sent Events."""
    config = {"configurable": {"thread_id": request.thread_id}}

    def event_stream():
        for event in graph.stream(
            {"messages": [("user", request.message)]},
            config=config,
            stream_mode="updates"
        ):
            for node_name, node_output in event.items():
                data = {"node": node_name, "content": ""}

                if "messages" in node_output:
                    messages = node_output["messages"]
                    if messages:
                        last_msg = messages[-1]
                        if hasattr(last_msg, "content"):
                            data["content"] = last_msg.content
                        elif isinstance(last_msg, tuple):
                            data["content"] = last_msg[1]

                yield f"data: {json.dumps(data)}\n\n"

        state = graph.get_state(config)
        if state.next:
            yield f"data: {json.dumps({'node': 'interrupt', 'content': 'Waiting for your input...', 'waiting_for_input': True})}\n\n"

        yield f"data: {json.dumps({'node': 'done', 'content': ''})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/resume/stream")
async def resume_stream(request: ResumeRequest):
    """Resume a paused graph with human feedback via streaming."""
    config = {"configurable": {"thread_id": request.thread_id}}

    state = graph.get_state(config)
    if not state.next:
        return {"error": "No pending interrupt for this session."}

    def event_stream():
        for event in graph.stream(
            Command(resume=request.feedback),
            config=config,
            stream_mode="updates"
        ):
            for node_name, node_output in event.items():
                data = {"node": node_name, "content": ""}
                if "messages" in node_output:
                    messages = node_output["messages"]
                    if messages:
                        last_msg = messages[-1]
                        if hasattr(last_msg, "content"):
                            data["content"] = last_msg.content
                        elif isinstance(last_msg, tuple):
                            data["content"] = last_msg[1]

                yield f"data: {json.dumps(data)}\n\n"

        yield f"data: {json.dumps({'node': 'done', 'content': ''})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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
