from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver


class FormState(TypedDict):
    age: int | None
    pending_question: str | None


def get_age_node(state: FormState):
    question = state.get("pending_question") or "What is your age?"
    answer = interrupt(question)
    print(f"I got {answer}")
    if isinstance(answer, int) and answer > 0:
        return {"age": answer, "pending_question": None}

    return {
        "pending_question": f"'{answer}' is not a valid age. Please enter a positive number."
    }


def route(state: FormState):
    return END if state.get("age") is not None else "collect age"


builder = StateGraph(FormState)
builder.add_node("collect_age", get_age_node)
builder.add_edge(START, "collect_age")
builder.add_conditional_edges("collect_age", route)

checkpointer = InMemorySaver()

graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "form-1"}}

first = graph.stream_events(
    {"age": None, "pending_question": None}, config=config, version="v3"
)

_ = first.output
print(first.interrupts)

# Provide invalid data; the node re-prompt via the conditional edge
retry = graph.stream_events(
    Command(resume="thirty"),
    config=config,
    version="v3",
)

_ = retry.output
print(retry.interrupts)

# Provide valid data; route() returns END and the graph finishes
final = graph.stream_events(Command(resume=50), config=config, version="v3")
print(final.output["age"])

with open("validate_human_input.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())
