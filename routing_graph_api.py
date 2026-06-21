from pydantic import BaseModel, Field
from typing_extensions import Literal, TypedDict
from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

prompt_api = os.getenv("test_api_key")

llm = ChatGroq(model="openai/gpt-oss-120b", api_key=prompt_api)


# Schema for structured output to use as routing logic
class Route(BaseModel):
    step: Literal["poem", "story", "joke"] = Field(
        None, description="The next step in the routing process."
    )


# Augment the llm with schema for structured output
route = llm.with_structured_output(Route)


# State
class State(TypedDict):
    input: str
    decision: str
    output: str


# Nodes
def llm_call_1(state: State):
    """Write a story"""
    result = llm.invoke(state["input"])

    return {"output": result.content}


def llm_call_2(state: State):
    """Write a poem"""
    result = llm.invoke(state["input"])

    return {"output": result.content}


def llm_call_3(state: State):
    """Write a joke"""
    result = llm.invoke(state["input"])

    return {"output": result.content}


def llm_call_router(state: State):
    """Route the input to the appropriate node."""

    # Run the augmented llm with structured output to serve as routing logic
    decision = route.invoke(
        [
            SystemMessage(
                content="Route the input to story, joke or poem based on the user's request."
            ),
            HumanMessage(content=state["input"]),
        ]
    )

    return {"decision": decision.step}


# Conditional edge function to route to the appropriate node
def route_decision(state: State):
    # Return the node name you want to visit next
    if state["decision"] == "story":
        return "llm_call_1"
    elif state["decision"] == "joke":
        return "llm_call_2"
    elif state["decision"] == "poem":
        return "llm_call_3"


# Build the workflow
router_builder = StateGraph(State)

router_builder.add_node("llm_call_1", llm_call_1)
router_builder.add_node("llm_call_2", llm_call_2)
router_builder.add_node("llm_call_3", llm_call_3)
router_builder.add_node("llm_call_router", llm_call_router)

router_builder.add_edge(START, "llm_call_router")
router_builder.add_conditional_edges(
    "llm_call_router",
    route_decision,
    {
        "llm_call_1": "llm_call_1",
        "llm_call_2": "llm_call_2",
        "llm_call_3": "llm_call_3",
    },
)

router_builder.add_edge("llm_call_1", END)
router_builder.add_edge("llm_call_2", END)
router_builder.add_edge("llm_call_3", END)

router_workflow = router_builder.compile()

png = router_workflow.get_graph().draw_mermaid_png()
with open("routing_graph_api.png", "wb") as f:
    f.write(png)

# Invoke
state = router_workflow.invoke({"input": "Write me a joke about cats"})
print(state["output"])
