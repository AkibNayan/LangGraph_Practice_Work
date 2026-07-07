from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, MessagesState
from langgraph_oracledb.checkpoint.oracle.aio import AsyncOracleSaver
from pathlib import Path
from dotenv import load_dotenv
import os
import asyncio

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("google_studio_api_key")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)

ORACLE_URI = "user/password@localhost:1521/FREEPDB1"


async def main():
    async with AsyncOracleSaver.from_conn_string(ORACLE_URI) as checkpointer:

        async def call_model(state: MessagesState):
            response = await llm.ainvoke(state["messages"])
            return {"messages": response}

        builder = StateGraph(MessagesState)
        builder.add_node(call_model)
        builder.add_edge(START, "call_model")

        graph = builder.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "1"}}

        stream = await graph.astream_events(
            {"messages": [{"role": "user", "content": "hi! I'm bob"}]},
            config,
            version="v3",
        )
        async for message in stream.messages:
            async for token in message.text:
                print(token, end="", flush=True)

        stream = await graph.astream_events(
            {"messages": [{"role": "user", "content": "what's my name?"}]},
            config,
            version="v3",
        )
        async for message in stream.messages:
            async for token in message.text:
                print(token, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
