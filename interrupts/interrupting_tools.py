import sqlite3
import operator
from typing import TypedDict, Literal, Annotated
from langchain.tools import tool
from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from langchain.messages import SystemMessage, AnyMessage, ToolMessage
from dotenv import load_dotenv
from pathlib import Path
import os

# Go up one directory from interrupts directory
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

groq_api_key = os.getenv("test_api_key")


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


@tool
def send_email(to: str, subject: str, body: str):
    """Send an email to the recipient."""
    # Pause before sending; payload surfaces on stream.interrupts when using event streaming
    response = interrupt(
        {
            "action": "send_email",
            "to": to,
            "subject": subject,
            "body": body,
            "message": "Approve sending this email?",
        }
    )

    if response.get("action") == "approve":
        # Resume value can override inputs before executing
        final_to = response.get("to", to)
        final_subject = response.get("subject", subject)
        final_body = response.get("body", body)

        # Actually send the email (Your implementation here)
        print(f"[send_email] to={final_to} subject={final_subject} body={final_body}")

        return f"Email sent to {final_to}"

    return "Email cancelled by user"


llm = ChatGroq(model="openai/gpt-oss-120b", api_key=groq_api_key)
llm_with_tools = llm.bind_tools([send_email])

tools_by_name = {"send_email": send_email}


def agent_node(state: AgentState):
    # LLM may decide to call the tool; interrupt pause before sending
    result = llm_with_tools.invoke(state["messages"])

    return {"messages": [result]}


def tool_node(state: AgentState):
    """Perform the tool call"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))

    return {"messages": result}


def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
    """Decide if we should continue the loop or stop
    based upon whether the llm made a tool call.
    """
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tool_node"
    return END


builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tool_node", tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, ["tool_node", END])
builder.add_edge("tool_node", "agent")

checkpointer = SqliteSaver(sqlite3.connect("tool-approval.db", check_same_thread=False))

graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "email-workflow"}}

initial = graph.stream_events(
    {
        "messages": [
            {
                "role": "user",
                "content": "Send an email to akibnayan182@gmail.com about the meeting",
            }
        ]
    },
    config=config,
    version="v3",
)

# drive the stream to completion
_ = initial.output
print(_)

print(initial.interrupts)

# Resume with approval and optionally edited arguments
resumed = graph.stream_events(
    Command(resume={"action": "approve", "subject": "Updated subject"}),
    config=config,
    version="v3",
)

# -> Tool result returned by send_email
print(resumed.output["messages"][-1])

# Show the workflow
with open("tool-approval.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())
