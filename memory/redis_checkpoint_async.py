from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("google_studio_api_key")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)

REDIS_URI = "redis://localhost:6379"


async def main():
    async with AsyncRedisSaver.from_conn_string(REDIS_URI) as checkpointer:

        async def call_model(state: MessagesState):
            response = await llm.ainvoke(state["messages"])
            return {"messages": response}

        builder = StateGraph(MessagesState)
        builder.add_node("call_model", call_model)
        builder.add_edge(START, "call_model")

        graph = builder.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "1"}}

        stream = await graph.astream_events(
            {"messages": [{"role": "user", "content": "Hi! I'm bob"}]},
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
