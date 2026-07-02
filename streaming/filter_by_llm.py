from typing import TypedDict
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END

# The joke model is tagged with joke
joke_model = init_chat_model(model="gpt-5.4-mini", tags=["joke"])
# The poem model is tagged with poem
poem_model = init_chat_model(model="gpt-5.4-mini", tags=["poem"])


class State(TypedDict):
    topic: str
    joke: str
    poem: str


config = {"configurable": {"thread_id": "1"}}


async def call_model(state: State, config):
    topic = state["topic"]
    print("Writing joke:")

    joke_response = await joke_model.ainvoke(
        {"messages": [{"role": "user", "content": f"Write a joke about {topic}"}]}
    )

    print("\n\nWriting poem:")
    poem_response = await poem_model.ainvoke(
        {"messages": [{"role": "user", "content": f"Write a poem about {topic}"}]}
    )

    return {"joke": joke_response.content, "poem": poem_response.content}


graph = StateGraph(State)
graph.add_node("call_model", call_model, config=config)
graph.add_edge(START, "call_model")
graph.add_edge("call_model", END)
graph = graph.compile()


async for chunk in graph.astream(
    {"topic": "ice cream"}, stream_mode="messages", version="v2"
):
    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]

        if metadata["tags"] == ["joke"]:
            print(msg.content, end="|", flush=True)
