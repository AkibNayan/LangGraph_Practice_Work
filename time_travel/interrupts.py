from langgraph.types import interrupt, Command
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    value: list[str]


def ask_human(state: State):
    answer = interrupt("What's your name?")
    return {"value": [f"Hello, {answer}"]}


def final_step(state: State):
    return {"value": ["Done"]}


graph = (
    StateGraph(State)
    .add_node("ask_human", ask_human)
    .add_node("final_step", final_step)
    .add_edge(START, "ask_human")
    .add_edge("ask_human", "final_step")
    .compile(checkpointer=InMemorySaver())
)

config = {"configurable": {"thread_id": "1"}}

# First run - hits interrupt
graph.invoke({"value": []}, config)
# Resume with answer
graph.invoke(Command(resume="Alice"), config)

# Replay from before ask_human
history = list(graph.get_state_history(config))

before_ask = [s for s in history if s.next == ("ask_human",)][-1]

replay_result = graph.invoke(None, before_ask.config)

# Fork from before ask-human
fork_config = graph.update_state(before_ask.config, {"value": ["forked"]})

fork_result = graph.invoke(None, fork_config)

# Resume the forked interrupt with a different answer
result = graph.invoke(Command(resume="Bob"), fork_config)
print(result)
