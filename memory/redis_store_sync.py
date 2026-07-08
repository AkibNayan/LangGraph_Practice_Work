from dataclasses import dataclass
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.redis import RedisSaver
from langgraph.store.redis import RedisStore
from langgraph.runtime import Runtime
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

gemini_api_key = os.getenv("google_studio_api_key")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=gemini_api_key)


@dataclass
class Context:
    user_id: str


def call_model(state: MessagesState, runtime: Runtime[Context]):
    user_id = runtime.context.user_id
    namespace = ("memories", user_id)

    memories = runtime.store.search(namespace, query=str(state["messages"][-1].content))
    info = "\n".join([d.value["data"] for d in memories])

    system_msg = f"You are a helpful assistant talking to the user. User info {info}"

    # Store new memory if the user asks to the model to remember
    last_message = state["messages"][-1]
    if "remember" in last_message.content.lower():
        memory = "User name is Bob"
        runtime.store.put(namespace, str(uuid.uuid4()), {"data": memory})

    response = llm.invoke(
        [{"role": "system", "content": system_msg}] + state["messages"]
    )

    return {"messages": response}


DB_URI = "redis://localhost:5432"

with (
    RedisStore.from_conn_string(DB_URI) as store,
    RedisSaver.from_conn_string(DB_URI) as checkpointer,
):
    store.setup()
    checkpointer.setup()

    builder = StateGraph(MessagesState, context_schema=Context)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "call_model")

    graph = builder.compile(store=store, checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "1"}}
    stream = graph.stream_events(
        {"messages": [{"role": "user", "content": "Hi! Remember: my name is Bob"}]},
        config,
        version="v3",
        context=Context(user_id="1"),
    )
    for snapshot in stream.values:
        snapshot["messages"][-1].pretty_print()

    config = {"configurable": {"thread_id": "2"}}
    stream = graph.stream_events(
        {"messages": [{"role": "user", "content": "what is my name?"}]},
        config,
        version="v3",
        context=Context(user_id="1"),
    )
    for snapshot in stream.values:
        snapshot["messages"][-1].pretty_print()
