from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, MessagesState
from pathlib import Path
from dotenv import load_dotenv
import os
from langchain.messages import RemoveMessage
from langgraph.checkpoint.memory import InMemorySaver

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

gemini_api_key = os.getenv("google_studio_api_key")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=gemini_api_key)


def delete_messages(state: MessagesState):
    messages = state["messages"]
    if len(messages) > 2:
        # remove the earliest 2 messages
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}


def call_model(state: MessagesState):
    response = llm.invoke(state["messages"])
    return {"messages": response}


checkpointer = InMemorySaver()

builder = StateGraph(MessagesState)
builder.add_sequence([call_model, delete_messages])
builder.add_edge(START, "call_model")

graph = builder.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "1"}}
stream = graph.stream_events(
    {"messages": [{"role": "user", "content": "Hi! I am bob"}]},
    config=config,
    version="v3",
)

for snapshot in stream.values:
    print([(message.type, message.content) for message in snapshot["messages"]])


stream = graph.stream_events(
    {"messages": [{"role": "user", "content": "what's my name?"}]}, config, version="v3"
)
for snapshot in stream.values:
    print([(message.type, message.content) for message in snapshot["messages"]])
