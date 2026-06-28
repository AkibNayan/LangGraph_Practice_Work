from langgraph.errors import NodeError
from langgraph.types import RetryPolicy, TimeoutPolicy
from langgraph.graph import StateGraph, START
from typing_extensions import TypedDict


class State(TypedDict):
    status: str


def default_error_handler(state: State, error: NodeError) -> State:
    return {"status": f"handled: {error.error}"}


graph = (
    StateGraph(State)
    .set_node_defaults(
        retry_policy=RetryPolicy(max_attempts=3),
        error_handler=default_error_handler,
        timeout=TimeoutPolicy(run_timeout=30),
    )
    # .add_node("step_a", step_a)
    # .add_node("step_b", step_b)
    .add_edge(START, "step_a")
    .compile()
)
