from typing import Any, TypedDict
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START

stream_model = ChatAnthropic(model_name="claude-haiku-4-5-20251001")
internal_model = ChatAnthropic(model_name="claude-haiku-4-5-20251001").with_config(
    {"tags": ["nostream"]}
)


class State(TypedDict):
    topic: str
    answer: str
    notes: str


def answer(state: State) -> dict[str, Any]:
    r = stream_model.invoke(
        [{"role": "user", "content": f"Reply briefly about {state['topic']}"}]
    )
    return {"answer": r.content}


def internal_notes(state: State) -> dict[str, Any]:
    r = internal_model.invoke(
        [{"role": "user", "content": f"Private notes on {state['topic']}"}]
    )
    return {"notes": r.content}


graph = StateGraph(State)
graph.add_node("write_answer", answer)
graph.add_node("internal_notes", internal_notes)
graph.add_edge(START, "write_answer")
graph.add_edge("write_answer", "internal_notes")
graph = graph.compile()


initial_state: State = {"topic": "AI", "answer": "", "notes": ""}

stream = graph.stream_events(initial_state, version="v3")
