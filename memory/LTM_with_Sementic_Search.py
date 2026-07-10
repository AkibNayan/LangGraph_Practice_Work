import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langgraph.store.memory import InMemoryStore
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.runtime import Runtime

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

semantic_api_key = os.getenv("semantic_api_key")

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=semantic_api_key)

# Create store with semantic search enabled
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
store = InMemoryStore(index={"embed": embeddings, "dims": 1536})

store.put(("user_123", "memories"), "1", {"text": "I love pizza"})
store.put(("user_123", "memories"), "2", {"text": "I am a plumber"})


async def main():
    async def chat(state: MessagesState, runtime: Runtime):
        # Search based on user's last message
        items = await runtime.store.asearch(
            ("user_123", "memories"), query=state["messages"][-1].content, limit=2
        )
        memories = "\n".join(item.value["text"] for item in items)
        memories = f"## Memories of user\n{memories}" if memories else ""
        response = await llm.ainvoke(
            [
                {"role": "system", "content": f"You are a helpful assistant.\n{memories}"},
                *state["messages"],
            ]
        )
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("chat", chat)
    builder.add_edge(START, "chat")
    graph = builder.compile(store=store)

    stream = await graph.astream_events(
        {"messages": [{"role": "user", "content": "I'm hungry"}]}, version="v3"
    )

    async for message in stream.messages:
        async for token in message.text:
            print(token, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
