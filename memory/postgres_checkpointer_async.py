from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pathlib import Path
from dotenv import load_dotenv
import os
import asyncio

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("test_api_key")

llm = ChatGroq(model="openai/gpt-oss-120b", api_key=api_key)

DB_URI = "postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable"


async def main():
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()

        async def call_model(state: MessagesState):
            response = await llm.ainvoke(state["messages"])
            return {"messages": response}

        builder = StateGraph(MessagesState)
        builder.add_node("call_model", call_model)
        builder.add_edge(START, "call_model")

        graph = builder.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "1"}}

        stream = await graph.astream_events(
            {"messages": [{"role": "user", "content": "hi! I'm bob"}]},
            config=config,
            version="v3",
        )

        async for message in stream.messages:
            async for token in message.text:
                print(token, end="", flush=True)

        stream = await graph.astream_events(
            {"messages": [{"role": "user", "content": "What's my name?"}]},
            config=config,
            version="v3",
        )

        async for message in stream.messages:
            async for token in message.text:
                print(token, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
