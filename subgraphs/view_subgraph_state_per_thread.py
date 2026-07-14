from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.memory import MemorySaver

subgraph_builder = StateGraph(MessagesState)

subgraph = subgraph_builder.compile(checkpointer=True)

builder = StateGraph(MessagesState)
builder.add_node("node_1", subgraph)
builder.add_edge(START, "node_1")

graph = builder.compile(checkpointer=MemorySaver())

config = {"configurable": {"thread_id": "1"}}

graph.invoke({"messages": [{"role": "user", "content": "hi"}]}, config=config)
graph.invoke(
    {"messages": [{"role": "user", "content": "What did I say?"}]}, config=config
)

# View accumulated subgraph state
subgraph_state = graph.get_state(config, subgraph=True).tasks[0].state
