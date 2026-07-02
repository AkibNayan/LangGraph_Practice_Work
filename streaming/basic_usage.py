from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer


class State(TypedDict):
    topic: str
    joke: str


def generate_joke(state: State):
    writer = get_stream_writer()
    writer({"status": "thinking of a joke..."})
    return {
        "joke": f"Why did the {state['topic']} go to school? To get a sundae education!"
    }


graph = StateGraph(State)
graph.add_node("generate_joke", generate_joke)
graph.add_edge(START, "generate_joke")
graph.add_edge("generate_joke", END)
graph = graph.compile()


for chunk in graph.stream(
    {"topic": "ice cream"}, stream_mode=["updates", "custom"], version="v2"
):
    if chunk["type"] == "updates":
        for node_name, state in chunk["data"].items():
            print(f"Node: {node_name} updated: {state}")
    elif chunk["type"] == "custom":
        print(f"Status: {chunk['data']['status']}")


for part in graph.stream(
    {"topic": "ice cream"},
    stream_mode=["values", "updates", "messages", "custom"],
    version="v2",
):
    if part["type"] == "values":
        # ValuesStreamPart - full state snapshot after each step
        print(f"State: topic={part['data']['topic']}")
    elif part["type"] == "updates":
        # UpdatesStreamPart - only the changed keys from each node
        for node_name, state in part["data"].items():
            print(f"Node: {node_name} updated: {state}")
    elif part["type"] == "messages":
        # MessagesStreamPart - messages from LLM calls
        msg, metadata = part["data"]
        print(msg.content, end="", flush=True)
    elif part["type"] == "custom":
        # CustomStreamPart - arbitrary data from get_stream_writer() calls
        pass
