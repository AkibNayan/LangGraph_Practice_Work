from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver
from typing_extensions import TypedDict


class State(TypedDict):
    foo: str


# Subgraphs
def subgraph_node1(state: State):
    return {"foo": state["foo"] + "bar"}


subgraph_builder = StateGraph(State)
subgraph_builder.add_node("subgraph_node1", subgraph_node1)
subgraph_builder.add_edge(START, "subgraph_node1")
subgraph = subgraph_builder.compile()

# Parent Graph
builder = StateGraph(State)
builder.add_node("node_1", subgraph)
builder.add_edge(START, "node_1")

checkpointer = InMemorySaver()

graph = builder.compile(checkpointer=checkpointer)
