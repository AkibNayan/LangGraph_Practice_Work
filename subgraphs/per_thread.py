from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("test_api_key")


@tool
def fruit_info(fruit_name: str) -> str:
    """Look up fruit info."""
    interrupt("continue?")
    return f"Info about {fruit_name}."


# Subagent with checkpointer=True for persistent state
fruit_agent = create_agent(
    model="llama-3.3-70b-versatile",
    api_key=api_key,
    tools=[fruit_info],
    system_prompt="You are a fruit expert. Use fruit info tool. Respond in one sentence.",
    checkpointer=True,
)


# Wrap subagent as a tool for the outer agent
@tool
def ask_fruit_expert(question: str) -> str:
    """Ask about fruit expert. Use for all fruit question."""
    response = fruit_agent.invoke({"messages": [{"role": "user", "content": question}]})

    return response["messages"][-1].content


# outer agent with checkpointer
# use ToolCallLimitMiddleware to prevent parallel calls to per_thread subagents
# which would cause checkpoint conflict
agent = create_agent(
    model="llama-3.3-70b-versatile",
    api_key=api_key,
    tools=[ask_fruit_expert],
    system_prompt="You have a fruit expert. Ask them questions about fruit.",
    middleware=[ToolCallLimitMiddleware(tool_name="ask_fruit_expert", run_limit=1)],
    checkpointer=MemorySaver(),
)

config = {"configurable": {"thread_id": "1"}}

# Stream events - the subagents tool call interrupts
stream = agent.stream_events(
    {"messages": [{"role": "user", "content": "Tell me about Apple"}]},
    config=config,
    version="v3",
)

output = stream.output

# Resume - the subagents tool call resumes
resumed = agent.stream_events(Command(resume=True), config=config, version="v3")

final = resumed.output
print(final)
