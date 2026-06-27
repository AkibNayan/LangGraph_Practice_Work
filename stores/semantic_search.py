from langchain.embeddings import init_embeddings
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
import uuid
from dataclasses import dataclass
from langgraph.graph import StateGraph, MessagesState
from langgraph.runtime import Runtime

store = InMemoryStore(
    index={
        "embed": init_embeddings("sentence-transformers/all-MiniLM-L6-v2"),
        "dims": 1536,
        "fields": ["food_preference", "$"],
    }
)

# Find memories about food preferences
# This can be done after putting memories into the store
memories = store.search(
    # namespace_for_memories,
    query="What does the user like to eat?",
    limit=3,
)

# Store with specific fields
store.put(
    # namespace_for_memories,
    str(uuid.uuid4()),
    {"food_preference": "I like italian cuisine", "context": "Discussing dinner plans"},
    index=["food_preference"],
)

# Store without embedding
store.put(
    # namespace_for_memories,
    str(uuid.uuid4()),
    {"system_info": "Last updated: 2024-01-01"},
    index=False,
)


@dataclass
class Context:
    user_id: str


# We need this because we want to enable threads
checkpointer = InMemorySaver()

builder = StateGraph(MessagesState, context_schema=Context)

graph = builder.compile(checkpointer=checkpointer, store=store)

# Invoke the graph
config = {"configurable": {"thread_id": "1"}}

# First lets just say hi to AI
for update in graph.stream(
    {"messages": [{"role": "user", "content": "hi"}]},
    config=config,
    stream_mode="updates",
    context=Context(user_id="1"),
):
    print(update)


async def update_memory(state: MessagesState, runtime: Runtime[Context]):
    user_id = runtime.context.user_id
    # namespace the memory
    namespace = (user_id, "memories")

    # Create a new memory ID
    memory_id = str(uuid.uuid4())

    # We create a new memory
    await runtime.store.aput(namespace, memory_id, {"memory": "memory"})


async def call_model(state: MessagesState, runtime: Runtime[Context]):
    user_id = runtime.context.user_id
    # namespace the memory
    namespace = (user_id, "memories")

    # Search based on the most recent messages
    memories = await runtime.store.asearch(
        namespace, query=state["messages"][-1].content, limit=3
    )

    info = "\n".join(d.value["memory"] for d in memories)


# Invoke the graph with a new thread
config = {"configurable": {"thread_id": "2"}}

for update in graph.stream(
    {"messages": [{"role": "user", "content": "hi tell me about my memories"}]},
    config=config,
    stream_mode="updates",
    context=Context(user_id="1"),
):
    print(update)
