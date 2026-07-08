from dataclasses import dataclass
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.store.redis.aio import AsyncRedisStore
from langgraph.runtime import Runtime
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

gemini_api_key = os.getenv("google_studio_api_key")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=gemini_api_key)


@dataclass
class Context:
    user_id: str


async def call_model(state: MessagesState, runtime: Runtime[Context]):
    user_id = runtime.context.user_id
    namespace = ("memories", user_id)

    memories = await runtime.store.asearch(
        namespace, query=str(state["messages"][-1].content)
    )
    info = "\n".join([d.value["data"] for d in memories])

    system_msg = f"You are a helpful assistant talking to the user. User info: {info}"

    # Store new memories if the user asks the model to remember
    last_message = state["messages"][-1]
    if "remember" in last_message.content.lower():
        memory = "User name is Bob"
        await runtime.store.aput(namespace, str(uuid.uuid4()), {"data": memory})

    response = await llm.ainvoke(
        [{"role": "system", "content": system_msg}] + state["messages"]
    )

    return {"messages": response}


DB_URI = "redis://localhost:6379"


async def main():
    async with (
        AsyncRedisStore.from_conn_string(DB_URI) as store,
        AsyncRedisSaver.from_conn_string(DB_URI) as checkpointer,
    ):
        # await store.setup()
        # await checkpointer.asetup()

        builder = StateGraph(MessagesState, context_schema=Context)
        builder.add_node(call_model)
        builder.add_edge(START, "call_model")

        graph = builder.compile(
            checkpointer=checkpointer,
            store=store,
        )

        config = {"configurable": {"thread_id": "1"}}
        stream = await graph.astream_events(
            {"messages": [{"role": "user", "content": "Hi! Remember: my name is Bob"}]},
            config,
            version="v3",
            context=Context(user_id="1"),
        )
        async for snapshot in stream.values:
            snapshot["messages"][-1].pretty_print()

        config = {"configurable": {"thread_id": "2"}}
        stream = await graph.astream_events(
            {"messages": [{"role": "user", "content": "what is my name?"}]},
            config,
            version="v3",
            context=Context(user_id="1"),
        )
        async for snapshot in stream.values:
            snapshot["messages"][-1].pretty_print()


if __name__ == "__main__":
    asyncio.run(main())
