from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, MessagesState
from langgraph_oracledb.checkpoint.oracle import OracleSaver
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("google_studio_api_key")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)

ORACLE_URI = "user/password@localhost:1521/FREEPDB1"

with OracleSaver.from_conn_string(ORACLE_URI) as checkpointer:

    def call_model(state: MessagesState):
        response = llm.invoke(state["messages"])
        return {"messages": response}

    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "call_model")

    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "1"}}

    stream = graph.stream_events(
        {"messages": [{"role": "user", "content": "Hi! my name is bob"}]},
        config=config,
        version="v3",
    )
    for snapshot in stream.values:
        print(snapshot)

    stream = graph.stream_events(
        {"messages": [{"role": "user", "content": "What's my name?"}]},
        config=config,
        version="v3",
    )
    for snapshot in stream.values:
        print(snapshot)
