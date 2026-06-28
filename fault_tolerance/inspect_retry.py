from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from langgraph.types import RetryPolicy
from typing_extensions import TypedDict


class State(TypedDict):
    result: str


def my_node(state: State, runtime: Runtime) -> State:
    if runtime.execution_info.node_attempt > 1:
        return {"result": "call_fallback_api()"}
    return {"result": "call_primary_api()"}


builder = StateGraph(State)
builder.add_node("my_node", my_node, retry_policy=RetryPolicy(max_attempts=3))
builder.add_edge(START, "my_node")
builder.add_edge("my_node", END)
