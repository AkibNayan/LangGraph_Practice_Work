import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.store.base import BaseStore
from langgraph_oracledb.store.oracle import OracleStore
from langgraph_oracledb.checkpoint.oracle import OracleSaver
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

gemini_api_key = os.getenv("google_studio_api_key")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=gemini_api_key)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

DB_URI = "user/password@localhost:1521/FREEPDB1"

with (
    OracleStore.from_conn_string(
        DB_URI, index={"embed": embeddings, "dims": 1536}
    ) as store,
    OracleSaver.from_conn_string(DB_URI) as checkpointer,
):
    store.setup()
    checkpointer.setup()

    def call_model(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
        user_id = config["configurable"]["user_id"]
        namespace = ("memories", user_id)

        memories = store.search(namespace, query=str(state["messages"][-1].content))
        info = "\n".join([d.values["data"] for d in memories])

        system_msg = (
            f"You are a helpful assistant talking to the user. User info {info}"
        )
        # Store new memories if the user asks to the model to remember
        last_message = state["messages"][-1]
        if "remember" in last_message.content.lower():
            memory = "User name is Bob"
            store.put(namespace, str(uuid.uuid4()), {"data": memory})

        response = llm.invoke(
            [{"role": "system", "content": system_msg}] + state["messages"]
        )

        return {"messages": response}

    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "call_model")

    graph = builder.compile(store=store, checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "1", "user_id": "1"}}
    stream = graph.stream_events(
        {"messages": [{"role": "user", "content": "Hi! Remember, my name is Bob"}]},
        config=config,
        version="v3",
    )
    for snapshot in stream.values:
        snapshot["messages"][-1].pretty_print()

    stream = graph.stream_events(
        {"messages": [{"role": "user", "content": "What is my name?"}]},
        config=config,
        version="v3",
    )

    for snapshot in stream.values:
        snapshot["messages"][-1].pretty_print()
