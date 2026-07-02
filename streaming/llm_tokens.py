from dataclasses import dataclass
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class MyState:
    topic: str
    joke: str = ""


groq_api = os.getenv("test_api_key")

model = ChatGroq(model_name="llama-3.3-70b-versatile", api_key=groq_api)


def call_model(state: MyState):
    """Call the LLM to generate a joke about a topic."""
    # Note that messages events are emitted even when the LLM is run using .invoke()
    model_response = model.invoke(
        {
            "messages": [
                {"role": "user", "content": f"Generate a joke about {state.topic}"}
            ]
        }
    )

    return {"joke": model_response.content}


graph = StateGraph(MyState)
graph.add_node("call_model", call_model)
graph.add_edge(START, "call_model")
graph = graph.compile()

# The "messages" stream mode streams LLM tokens with metadata
# Use version="v2" for a unified StreamPart format
for chunk in graph.stream({"topic": "ice cream"}, stream_mode="messages", version="v2"):
    if chunk["type"] == "messages":
        messages_chunk, metadata = chunk["data"]
        if messages_chunk.content:
            print(messages_chunk.content, end="", flush=True)
