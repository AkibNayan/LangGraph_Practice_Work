from typing import TypedDict
from langgraph.graph import StateGraph, START
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model_name="gpt-5.4-mini")


class State(TypedDict):
    topic: str
    joke: str
    poem: str


def write_joke(state: State):
    topic = state["topic"]
    joke_response = model.invoke(
        [{"role": "user", "content": f"Write a joke about {topic}"}]
    )

    return {"joke": joke_response.content}


def write_poem(state: State):
    topic = state["topic"]
    poem_response = model.invoke(
        [{"role": "user", "content": f"Write a poem about {topic}"}]
    )
    return {"poem": poem_response.content}


graph = StateGraph(State)
graph.add_node("write_joke", write_joke)
graph.add_node("write_poem", write_poem)
graph.add_edge(START, "write_joke")
graph.add_edge("write_joke", "write_poem")
graph = graph.compile()


for chunk in graph.stream({"topic": "cats"}, stream_mode="messages", version="v2"):
    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        print(msg.content, end="", flush=True)
