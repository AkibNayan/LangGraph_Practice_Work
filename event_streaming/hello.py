from langgraph.graph import StateGraph, START, END
from typing import TypedDict
import asyncio
from langgraph.types import Command


class State(TypedDict):
    result: int


def multiply(a: int, b: int) -> int:
    return {"result": a * b}


builder = StateGraph(State)
builder.add_node("multiply", multiply)
builder.add_edge(START, "multiply")
builder.add_edge("multiply", END)
graph = builder.compile()

stream = graph.stream_events(
    {"messages": [{"role": "user", "content": "what is 42 * 17"}]}, version="v3"
)

for message in stream.messages:
    for token in message.text:
        print(token, end="", flush=True)

final_state = stream.output
print(final_state)


for subgraph in stream.subgraphs:
    print(subgraph.graph_name, subgraph.path)

    for message in subgraph.messages:
        print(message.text)

for snapshot in stream.values:
    print(snapshot)

# print(stream.output)

stream = await graph.astream_events(
    {"messages": [{"role": "user", "content": "what is 42 * 17"}]}, version="v3"
)


async def consume_messages():
    async for message in stream.messages:
        print(f"[llm] node: {message.node}")


async def consume_subgraphs():
    async for subgraph in stream.subgraphs:
        print(f"[subgraph] path= {subgraph.path}")


await asyncio.gather(consume_messages(), consume_subgraphs())


for name, item in stream.interleave("values", "messages", "subgraphs"):
    if name == "values":
        print(f"[state] keys= {list(item)}")
    elif name == "messages":
        print(f"[llm] node: {item.node}")
    elif name == "subgraphs":
        print(f"[subgraph] path= {item.path}")


for message in stream.messages:
    print(message.text)

if stream.interrupted:
    print(stream.interrupts)

stream = graph.stream_events(
    Command(resume={"decisions": [{"type": "approve"}]}), version="v3"
)

final_state = stream.output
print(final_state)


for event in stream:
    namespace = event["params"]["namespace"]
    print(namespace, event["method"], event["params"]["data"])

