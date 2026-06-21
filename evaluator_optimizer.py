from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Literal
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

test_api_key = os.getenv("test_api_key")

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=test_api_key)


# Graph State
class State(TypedDict):
    joke: str
    topic: str
    feedback: str
    funny_or_not: str


# schema for structured output to use in evaluation
class Feedback(BaseModel):
    grade: Literal["funny", "not_funny"] = Field(
        description="Decide if the joke is funny or not!"
    )
    feedback: str = Field(
        description="If the joke is not funny, provide feedback on how to improve it."
    )


# Augment llm with schema for structured output
evaluator = llm.with_structured_output(Feedback)


# Nodes
def llm_call_generator(state: State):
    """LLM generates a joke"""
    if state.get("feedback"):
        msg = llm.invoke(
            f"Write a joke about {state['topic']} but take into account the feedback: {state['feedback']}"
        )
    else:
        msg = llm.invoke(f"Write a joke about {state['topic']}")

    return {"joke": msg}


def llm_call_evaluator(state: State):
    """LLM evaluates the joke"""
    grade = evaluator.invoke(f"Grade the joke {state['joke']}")

    return {"funny_or_not": grade.grade, "feedback": grade.feedback}


# Conditional edge function to route back to joke generator or end based upon feedback from evaluator
def route_joke(state: State):
    """Route back to joke generator or end based upon feedback from evaluator"""
    if state["funny_or_not"] == "funny":
        return "Accepted"
    elif state["funny_or_not"] == "not funny":
        return "Rejected + Feedback"


# Build workflow
optimizer_builder = StateGraph(State)

# Add the nodes
optimizer_builder.add_node("llm_call_generator", llm_call_generator)
optimizer_builder.add_node("llm_call_evaluator", llm_call_evaluator)

# Add edges to connect node
optimizer_builder.add_edge(START, "llm_call_generator")
optimizer_builder.add_edge("llm_call_generator", "llm_call_evaluator")
optimizer_builder.add_conditional_edges(
    "llm_call_evaluator",
    route_joke,
    {  # Name returned by route_joke : Name of next node to visit
        "Accepted": END,
        "Rejected + Feedback": "llm_call_generator",
    },
)

# compile the workflow
optimizer_workflow = optimizer_builder.compile()

# Show the workflow
png = optimizer_workflow.get_graph().draw_mermaid_png()
with open("evaluator_optimizer_workflow.png", "wb") as f:
    f.write(png)

# Invoke
state = optimizer_workflow.invoke({"topic": "cats"})
print(state["joke"])
