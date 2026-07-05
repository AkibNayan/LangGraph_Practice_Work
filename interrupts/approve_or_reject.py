from typing import Literal, TypedDict, Optional
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt


class ApprovalState(TypedDict):
    action_details: str
    status: Optional[Literal["pending", "approved", "rejected"]]


def approval_node(state: ApprovalState) -> Command[Literal["proceed", "cancel"]]:
    # Expose detail so the caller can render them in an UI
    decision = interrupt(
        {"question": "Approve this action?", "details": state["action_details"]}
    )

    # Route to the appropriate node after resume
    return Command(goto="proceed" if decision else "cancel")


def proceed_node(state: ApprovalState):
    return {"status": "approved"}


def cancel_node(state: ApprovalState):
    return {"status": "rejected"}


graph = (
    StateGraph(ApprovalState)
    .add_node("approval", approval_node)
    .add_node("proceed", proceed_node)
    .add_node("cancel", cancel_node)
    .add_edge(START, "approval")
    .add_edge("proceed", END)
    .add_edge("cancel", END)
)


# Use a more durable checkpointer in production
checkpointer = InMemorySaver()
graph = graph.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "approval-123"}}

initial = graph.stream_events(
    {"action_details": "Transfer $500", "status": "pending"},
    config=config,
    version="v3",
)

# Drive the stream to completion
_ = initial.output

# -> (Interrupt(value={'question': ..., 'details': ...}),)
print(initial.interrupts)

# Resume with the decision; True route to proceed, False to cancel
resumed = graph.stream_events(Command(resume=True), config=config, version="v3")

print(resumed.output["status"])

with open("approve_or_rejected.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())