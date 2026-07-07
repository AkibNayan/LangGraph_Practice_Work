from dataclasses import dataclass
from langgraph.runtime import Runtime
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.store.memory import InMemoryStore
import uuid


@dataclass
class Context:
    user_id: str


async def call_model(state: MessagesState, runtime: Runtime[Context]):
    user_id = runtime.context.user_id
    namespace = (user_id, "memories")

    # Search for relevant memories
    memories = await runtime.store.asearch(
        namespace, query=state["messages"][-1].content, limit=3
    )

    info = "\n".join([d.value["data"] for d in memories])

    # ... use memories in model call

    # store a new memory
    await runtime.store.aput(
        namespace, str(uuid.uuid4()), {"data": "User prefers dark mode"}
    )


builder = StateGraph(MessagesState, context_schema=Context)
builder.add_node("call_model", call_model)
builder.add_edge(START, "call_model")

store = InMemoryStore()

graph = builder.compile(store=store)

# Pass context at invocation time
# Every time when you invoke always pass context data
graph.invoke(
    {"messages": [{"role": "user", "content": "hi"}]},
    config={"configurable": {"thread_id": "1"}},
    context=Context(user_id="1"),
)
