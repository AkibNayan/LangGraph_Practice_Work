import operator
import json
from typing import TypedDict
from typing_extensions import Annotated
from langgraph.graph import StateGraph, START
from openai import AsyncOpenAI

openai_client = AsyncOpenAI()

model_name = "gpt-5.4-mini"


async def stream_tokens(model_name: str, messages: list[dict]):
    response = openai_client.chat.completions.create(
        messages=messages, model=model_name, stream=True
    )

    role = None
    async for chunk in response:
        delta = chunk.choices[0].delta

        if delta.role is not None:
            role = delta.role

        if delta.content:
            yield {"role": role, "content": delta.content}


# This is our tool
async def get_items(place: str) -> str:
    """Use this tool to get items one might find in a place you're asked about."""
    writer = get_stream_writer()
    response = ""

    async for msg_chunk in stream_tokens(
        model_name,
        [
            {
                "role": "user",
                "content": (
                    "Can you tell me what kind of items"
                    f"i might find in the following place: {place}"
                    "List at least 3 such items separating them by a comma."
                    "And include a brief description of each item"
                ),
            }
        ],
    ):
        response += msg_chunk["content"]
        writer(msg_chunk)

    return response


class State(TypedDict):
    messages: Annotated[list[dict], operator.add]


# this is the tool calling graph node
async def call_tool(state: State):
    ai_message = state["messages"][-1]
    tool_call = ai_message["tool_call"][-1]

    function_name = tool_call["function"]["name"]

    if function_name != "get_items":
        raise ValueError(f"Tool {function_name} is not supported")

    function_arguments = tool_call["function"]["arguments"]
    arguments = json.loads(function_arguments)

    function_response = await get_items(**arguments)
    tool_message = {
        "tool_call_id": tool_call["id"],
        "role": "tool",
        "name": function_name,
        "content": function_response,
    }

    return {"messages": [tool_message]}


graph = StateGraph(State).add_node(call_tool).add_edge(START, "call_tool").compile()


inputs = {
    "messages": [
        {
            "content": None,
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "1",
                    "function": {
                        "arguments": '{"place": "bedroom}',
                        "name": "get_items",
                    },
                    "type": "function",
                }
            ],
        }
    ]
}

for chunk in graph.astream(inputs, stream_mode="custom", version="v2"):
    if chunk["type"] == "custom":
        print(chunk["data"]["content"], end="|", flush=True)
