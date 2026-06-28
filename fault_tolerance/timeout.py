from langgraph.graph import StateGraph, START
from datetime import timedelta
from langgraph.types import TimeoutPolicy
from langgraph.runtime import Runtime

from typing_extensions import TypedDict


class State(TypedDict):
    result: str


def call_model(state: State, runtime: Runtime) -> State:
    if runtime.execution_info.node_attempt > 1:
        return {"result": "call_fallback_api()"}
    return {"result": "call_primary_api()"}


# Simple wall clock cap
builder = StateGraph()

builder.add_node("call_model", call_model, timeout=60)
builder.add_node("call_model", call_model, timeout=timedelta(minutes=2))

builder.add_node("call_model", call_model, timeout=TimeoutPolicy(
    run_timeout=120,
    idle_timeout=30
))

