from src.graph.graph import build_graph

graph = build_graph()

config = {"configurable": {"thread_id": "test-session-1"}}

response = graph.invoke(
    {
        "messages": [("user","Find me a AI Engineer jobs in California")]
    },
    config = config
)

print(response["messages"][-1].content)