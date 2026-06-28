from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from langgraph.types import TimeoutPolicy
from typing_extensions import TypedDict


class State(TypedDict):
    result: str


async def long_running_node(state: State, runtime: Runtime) -> State:
    """# for batch in fetch_batches():
        # process(batch)
        # runtime.heartbeat()
    # return {"result": "done"}"""
    pass


builder = StateGraph(State)

builder.add_node(
    "long_running_node",
    long_running_node,
    timeout=TimeoutPolicy(idle_timeout=30, refresh_on="heartbeat"),
)

builder.add_edge(START, "long_running_node")
builder.add_edge("long_running_node", END)
