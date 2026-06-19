from src.graph.graph import build_graph
from langgraph.types import Command

graph = build_graph()

config = {"configurable": {"thread_id": "test-session-1"}}

response = graph.invoke(
    {
        "messages": [("user","Find me a data engineer jobs in Dallas")]
    },
    config = config
)

print(response["messages"][-1].content)

state = graph.get_state(config)

if state.next:
    print("\n----- HUMAN IN THE LOOP ------\n")
    print("Agent paused, waiting for your input")

    human_input = input("Approved (yes/no): ")

    response = graph.invoke(
        Command(resume=human_input),
        config=config
    )

    print(response["messages"][-1].content)