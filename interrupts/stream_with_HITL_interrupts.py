from langgraph.types import Command
from langgraph.graph import StateGraph

graph = StateGraph()

stream_input: dict | Command = initial_input
config = {"configurable": {"thread_id": "thread-1"}}

while True:
    stream = graph.stream_events(stream_input, config=config, version="v3")
    # Stream LLM response chunk (including any in subgraphs) as they arrive

    for message in stream.messages:
        for token in message.text:
            display_streaming_content(token)

    # After the finishes (or pause), check for interrupts and resume
    if not stream.interrupted:
        final_state = stream.output
        break

    interrupt_info = stream.interrupts[0].values
    user_response = get_user_input(interrupt_info)
    stream_input = Command(resume=user_response)
