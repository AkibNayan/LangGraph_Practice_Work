from typing import Annotated, TypedDict
import operator
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt


class State(TypedDict):
    vals: Annotated[list[str], operator.add]


def node_a(state):
    answer = interrupt("question_a")
    return {"vals": [f"a: {answer}"]}


def node_b(state):
    answer = interrupt("question_b")
    return {"vals": [f"b: {answer}"]}


graph = (
    StateGraph(State)
    .add_node("a", node_a)
    .add_node("b", node_b)
    .add_edge(START, "a")
    .add_edge(START, "b")
    .add_edge("a", END)
    .add_edge("b", END)
    .compile(checkpointer=InMemorySaver())
)

config = {"configurable": {"thread_id": "1"}}

# Step 1: Stream events to drive the run; both parallel node hit interrupts() and pause
stream = graph.stream_events({"vals": []}, config=config, version="v3")
_ = stream.output  # Drive the stream to completion
# stream.interrupts contains the pending interrupt payloads

print(stream.interrupts)

# Step 2: Resume all pending interrupts at once
resume_map = {i.id: f"answer for: {i.value}" for i in stream.interrupts}

resumed = graph.stream_events(Command(resume=resume_map), config=config, version="v3")

print("Final State: ", resumed.output)
