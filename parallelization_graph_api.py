from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

parallel_api = os.getenv("test_api_key")

llm = ChatGroq(model="openai/gpt-oss-120b", api_key=parallel_api)


class State(TypedDict):
    topic: str
    joke: str
    story: str
    poem: str
    combined_output: str


# Nodes
def call_llm_1(state: State):
    """First LLM call to generate initial joke."""
    msg = llm.invoke(f"Write a joke about {state['topic']}")

    return {"joke": msg.content}


def call_llm_2(state: State):
    """Second LLM call to generate story."""
    msg = llm.invoke(f"Write a story about {state['topic']}")

    return {"story": msg.content}


def call_llm_3(state: State):
    """Third LLM call to generate poem."""
    msg = llm.invoke(f"Write a poem about {state['topic']}")

    return {"poem": msg.content}


def aggregator(state: State):
    """Combine the joke, store, poem into a single output."""

    combined = f"Here is a story, joke and poem about {state['topic']}!\n\n"
    combined += f"STORY:\n{state['story']}\n\n"
    combined += f"JOKE:\n{state['joke']}\n\n"
    combined += f"POEM:\n{state['poem']}"

    return {"combined_output": combined}


# Build workflow
parallel_builder = StateGraph(State)

# Add Node
parallel_builder.add_node("call_llm_1", call_llm_1)
parallel_builder.add_node("call_llm_2", call_llm_2)
parallel_builder.add_node("call_llm_3", call_llm_3)
parallel_builder.add_node("aggregator", aggregator)

# Add Edges
parallel_builder.add_edge(START, "call_llm_1")
parallel_builder.add_edge(START, "call_llm_2")
parallel_builder.add_edge(START, "call_llm_3")

parallel_builder.add_edge("call_llm_1", "aggregator")
parallel_builder.add_edge("call_llm_2", "aggregator")
parallel_builder.add_edge("call_llm_3", "aggregator")

parallel_builder.add_edge("aggregator", END)

# Compile workflow
parallel_workflow = parallel_builder.compile()

# Show the workflow
png = parallel_workflow.get_graph().draw_mermaid_png()
with open("parallel_workflow.png", "wb") as f:
    f.write(png)

state = parallel_workflow.invoke({"topic": "tiger"})
print(state["combined_output"])
