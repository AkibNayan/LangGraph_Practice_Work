from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

checkpointer = InMemorySaver()

builder = StateGraph(...)

graph = builder.compile(checkpointer=checkpointer)

graph.invoke(
    {"messages": [{
        "role": "user",
        "content": "hi! I am Bob!"
    }]},
    config={"configurable": {"thread_id": "1"}}
)
