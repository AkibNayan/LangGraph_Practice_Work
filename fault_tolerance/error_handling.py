from langgraph.errors import NodeError
from langgraph.types import RetryPolicy, Command
from langgraph.graph import StateGraph, START
from typing_extensions import TypedDict


class State(TypedDict):
    result: str


def charge_payment(state: State) -> State:
    raise RuntimeError("payment gateway timeout")


def payment_error_handler(state: State, error: NodeError) -> Command:
    return Command(update={"status": f"compensated: {error.error}"}, goto="finalize")


def finalize(state: State) -> State:
    return state


graph = (
    StateGraph(State)
    .add_node(
        "charge_payment",
        charge_payment,
        retry_policy=RetryPolicy(max_attempts=3, retry_on=ConnectionError),
        error_handler=payment_error_handler,
    )
    .add_node("finalize", finalize)
    .add_edge(START, "charge_payment")
    .compile()
)
