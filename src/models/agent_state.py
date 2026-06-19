from typing_extensions import TypedDict
from typing import Annotated, Optional, Literal
from langgraph.graph import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str
    current_agent: str
    human_feedback: Optional[str]
    approved: Optional[str]

