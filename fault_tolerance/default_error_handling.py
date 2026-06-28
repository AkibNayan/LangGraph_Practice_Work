from langgraph.errors import NodeError
from langgraph.graph import StateGraph, START
from langgraph.types import RetryPolicy
from typing_extensions import TypedDict


class State(TypedDict):
    status: str


def always_failing(state: State) -> State:
    raise ValueError("something went wrong")


def default_handler(state: State, error: NodeError) -> State:
    return {"status": f"recovered from {error.node}: {error.error}"}


graph = (
    StateGraph(State)
    .set_node_defaults(
        retry_policy=RetryPolicy(max_attempts=3), error_handler=default_handler
    )
    .add_node("always_failing", always_failing)
    .add_edge(START, "always_failing")
    .compile()
)
