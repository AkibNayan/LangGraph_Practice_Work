from typing import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import AnyMessage
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.checkpoint.memory import InMemorySaver
from langmem.short_term import SummarizationNode, RunningSummary
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

gemini_api_key = os.getenv("google_studio_api_key")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=gemini_api_key)
summarization_llm = llm.bind(max_tokens=128)


class State(MessagesState):
    context: dict[str, RunningSummary]


class LLMInputState(TypedDict):
    summarized_messages: list[AnyMessage]
    context: dict[str, RunningSummary]


summarization_node = SummarizationNode(
    token_counter=count_tokens_approximately,
    model=summarization_llm,
    max_tokens=256,
    max_tokens_before_summary=256,
    max_summary_tokens=128,
)


def call_model(state: LLMInputState):
    response = llm.invoke(state["summarized_messages"])
    return {"messages": response}


checkpointer = InMemorySaver()

builder = StateGraph(State)
builder.add_node("call_model", call_model)
builder.add_node("summarize", summarization_node)
builder.add_edge(START, "summarize")
builder.add_edge("summarize", "call_model")
graph = builder.compile(checkpointer=checkpointer)

# Invoke the graph
config = {"configurable": {"thread_id": "1"}}
graph.invoke({"messages": "hi, my name is bob"}, config)
graph.invoke({"messages": "write a short poem about cats"}, config)
graph.invoke({"messages": "now do the same but for dogs"}, config)
final_response = graph.invoke({"messages": "what's my name?"}, config)

final_response["messages"][-1].pretty_print()
