from langchain.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import MessagesState, StateGraph


@tool
def search(query: str) -> str:
    """Search for information"""
    return f"Results for {query}"


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression"""
    return str(eval(expression))


graph = StateGraph(MessagesState)
graph.add_node("tools", ToolNode([search, calculator]))

graph = graph.compile()
