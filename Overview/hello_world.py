from langgraph.graph import StateGraph, MessagesState, START, END
from IPython.display import Image, display


def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "Hello, world!"}]}


graph = StateGraph(MessagesState)
graph.add_node("mock_llm", mock_llm)
graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)
graph = graph.compile()

result = graph.invoke({"messages": [{"role": "user", "content": "hi"}]})
# print(result)

# 1. Print the graph structure as Mermaid text
print(graph.get_graph().draw_mermaid())

# 2. Display the workflow diagram in Jupyter Notebook
# print(display(graph.get_graph().draw_mermaid_png()))

# 3. Print the nodes
print(graph.get_graph().nodes)