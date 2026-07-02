from typing import TypedDict
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph, START


class State(TypedDict):
    query: str
    answer: str


def node(state: State):
    writer = get_stream_writer()
    writer({"custom_key": "Generating custom data inside node."})
    return {"answer": "some data"}


graph = StateGraph(State)
graph.add_node("node", node)
graph.add_edge(START, "node")
graph = graph.compile()

inputs = {"query": "Example"}

for chunk in graph.stream(inputs, stream_mode="custom", version="v2"):
    if chunk["type"] == "custom":
        print(f"Custom event: {chunk['data']['custom_key']}")
