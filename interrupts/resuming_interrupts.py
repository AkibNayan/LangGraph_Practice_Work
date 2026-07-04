from langgraph.types import Command
from langgraph.graph import StateGraph

graph = StateGraph()

# Initial run hits the interrupt and pauses
# thread_id is the persistent pointer (stores a stable ID in production)
config = {"configurable": {"thread_id": "thread_1"}}
stream = graph.stream_events({"input": "data"}, config=config, version="v3")

# Drain the stream to drive the run, stream.output awaits the final state
final = stream.output

# stream.interrupted is True when the run paused for human input and
# stream.interrupts contain the payload passed to interrupt().

if stream.interrupted:
    print(stream.interrupts)

    # > (Interrupt(value="Do you approve this action?"))

# Resumes with the humans response
# The resume payload becomes the return value of interrupt() inside the node
resumed = graph.stream_events(Command(resume=True), config=config, version="v3")
final = resumed.output
