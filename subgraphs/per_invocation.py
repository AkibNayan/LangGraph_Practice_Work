from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt


@tool
def fruit_info(fruit_name: str) -> str:
    """Look up fruit info"""
    interrupt("continue?")
    return f"Info about {fruit_name}"


@tool
def veggie_info(veggie_name: str) -> str:
    """Look up veggie info"""
    return f"Info about {veggie_name}"


# subagents no checkpointer setting (inherits parent)
fruit_agent = create_agent(
    model="llama-3.3-70b-versatile",
    tools=[fruit_info],
    prompt="You are a fruit expert. Use fruit info tool. Respond in one sentence.",
)


veggie_agent = create_agent(
    model="llama-3.3-70b-versatile",
    tools=[veggie_info],
    prompt="You are a vegetable expert. Use veggie info tool. Respond in one sentence.",
)


# Wrap subagents as tools for the outer agent.
@tool
def ask_fruit_expert(question: str) -> str:
    """Ask the fruit expert. Use for all fruit question."""
    response = fruit_agent.invoke({"messages": [{"role": "user", "content": question}]})

    return response["messages"][-1].content


@tool
def ask_veggie_expert(question: str) -> str:
    """Ask the vegetable expert. Use for all vegetable question."""
    response = veggie_agent.invoke(
        {"messages": [{"role": "user", "content": question}]}
    )

    return response["messages"][-1].content


# Outer agent with checkpointer
agent = create_agent(
    model="llama-3.3-70b-versatile",
    tools=[ask_fruit_expert, ask_veggie_expert],
    prompt=(
        "You have two experts: ask_fruit_expert and ask_veggie_expert. "
        "ALWAYS delegate questions to the appropriate expert."
    ),
    checkpointer=MemorySaver(),
)

config = {"configurable": {"thread_id": "1"}}

# Stream event's - the subagents tool call interrupts
stream = agent.stream_events(
    {"messages": [{"role": "user", "content": "Tell me about Apple"}]},
    config=config,
    version="v3",
)

output = stream.ouput  # drive the stream to completion
# stream.interrupts contains pending interrupts

# Resume approved the interrupt
resumed = agent.stream_events(Command(resume=True), config=config, version="v3")
final = resumed.output

print(final)
