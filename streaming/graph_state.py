from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    topic: str
    joke: str


def refine_topic(state: State):
    return {"topic": state["topic"] + " and cats"}


def generate_joke(state: State):
    return {"joke": f"This is a joke about {state['topic']}"}


graph = StateGraph(State)
graph.add_node("refine_topic", refine_topic)
graph.add_node("generate_joke", generate_joke)
graph.add_edge(START, "refine_topic")
graph.add_edge("refine_topic", "generate_joke")
graph.add_edge("generate_joke", END)

graph = graph.compile()


for chunk in graph.stream({"topic": "ice cream"}, stream_mode="updates", version="v2"):
    if chunk["type"] == "updates":
        for node_name, state in chunk["data"].items():
            print(f"Node {node_name} updated to {state}")


for chunk in graph.stream({"topic": "ice cream"}, stream_mode="values", version="v2"):
    if chunk["type"] == "values":
        print(f"topic: {chunk['data']['topic']}")
