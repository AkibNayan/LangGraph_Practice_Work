from langchain.tools import tool
import os
from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain.messages import SystemMessage, HumanMessage, ToolMessage
from typing_extensions import Literal

load_dotenv()

test_api_key = os.getenv("test_api_key")
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=test_api_key)


# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a / b


# augment the llm with tools
tools = [multiply, add, divide]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)


# Nodes
def llm_call(state: MessagesState):
    """LLM decides whether to call a tool or not."""
    return {
        "messages": llm_with_tools.invoke(
            [
                SystemMessage(
                    content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                )
            ]
            + state["messages"]
        )
    }


def tool_node(state: MessagesState):
    """Performs the tool call."""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))

    return {"messages": result}


# Conditional edges function to route to the tool node or end based upon whether the llm made a tool call
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the llm made a tool call."""
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tool_node"
    else:
        return END


# Build the workflow
agent_builder = StateGraph(MessagesState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])

agent_builder.add_edge("tool_node", "llm_call")

agent = agent_builder.compile()

png = agent.get_graph().draw_mermaid_png()
with open("agent_with_tools.png", "wb") as f:
    f.write(png)

# Invoke
messages = [HumanMessage(content="What is 2 times 3?")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()
