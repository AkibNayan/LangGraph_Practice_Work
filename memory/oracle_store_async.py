import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.store.base import BaseStore
from langgraph_oracledb.store.oracle.aio import AsyncOracleStore
from langgraph_oracledb.checkpoint.oracle.aio import AsyncOracleSaver
from pathlib import Path
from dotenv import load_dotenv
import os
import asyncio

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

gemini_api_key = os.getenv("google_studio_api_key")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=gemini_api_key)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

DB_URI = "user/password@localhost:1521/FREEPDB1"


async def main():
    async with (
        AsyncOracleStore.from_conn_string(
            DB_URI, index={"embed": embeddings, "dims": 1536}
        ) as store,
        AsyncOracleSaver.from_conn_string(DB_URI) as checkpointer,
    ):
        await store.setup()
        await checkpointer.setup()

        async def call_model(
            state: MessagesState, config: RunnableConfig, *, store: BaseStore
        ):
            user_id = config["configurable"]["user_id"]
            namespace = ("memories", user_id)
            memories = await store.search(
                namespace, query=str(state["messages"][-1].content)
            )
            info = "\n".join([d.values["data"] for d in memories])

            system_msg = (
                f"You are a helpful assistant talking to the user. User info: {info}"
            )
            # Store new memories if the user asks the model to remember
            last_message = state["messages"][-1]
            if "remember" in last_message.content.lower():
                memory = "User name is Bob"
                await store.aput(namespace, str(uuid.uuid4()), {"data": memory})

            response = await llm.ainvoke(
                [{"role": "system", "content": system_msg}] + state["messages"]
            )
            return {"messages": response}

        builder = StateGraph(MessagesState)
        builder.add_node(call_model)
        builder.add_edge(START, "call_model")

        graph = builder.compile(
            checkpointer=checkpointer,
            store=store,
        )

        config = {
            "configurable": {
                "thread_id": "1",
                "user_id": "1",
            }
        }
        stream = await graph.astream_events(
            {"messages": [{"role": "user", "content": "Hi! Remember: my name is Bob"}]},
            config,
            version="v3",
        )
        async for snapshot in stream.values:
            snapshot["messages"][-1].pretty_print()

        config = {
            "configurable": {
                "thread_id": "2",
                "user_id": "1",
            }
        }

        stream = await graph.astream_events(
            {"messages": [{"role": "user", "content": "what is my name?"}]},
            config,
            version="v3",
        )
        async for snapshot in stream.values:
            snapshot["messages"][-1].pretty_print()


if __name__ == "__main__":
    asyncio.run(main())
