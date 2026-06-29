from langgraph.config import get_stream_writer
from langgraph.stream import ProtocolEvent, StreamTransformer, StreamChannel
from langgraph.graph import StateGraph, START, END
from typing import TypedDict


class State(TypedDict):
    result: int


def multiply(a: int, b: int) -> int:
    return {"result": a * b}


builder = StateGraph(State)
builder.add_node("multiply", multiply)
builder.add_edge(START, "multiply")
builder.add_edge("multiply", END)
graph = builder.compile()


def node(state):

    writer = get_stream_writer()
    writer({"kind": "progress", "message": "retrieving context"})
    return state


class CustomTransformer(StreamTransformer):
    required_stream_modes = ("tools",)

    def __init__(self, scope: tuple[str, ...] = ()) -> None:
        super().__init__(scope)
        self.log = StreamChannel()

    def init(self) -> dict:
        return {"custom": self.log}

    def process(self, event: ProtocolEvent) -> ProtocolEvent:
        if event["method"] == "custom":
            self.log.push(event["params"]["data"])
        return True


stream = graph.stream_events(
    {"messages": [{"role": "user", "content": "multiply 2 by 3"}]},
    version="v3",
    transformers=[CustomTransformer],
)

for item in stream.extension["custom"]:
    print(item)
