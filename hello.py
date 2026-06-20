import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

load_dotenv()

test_api_key = os.getenv("test_api_key")
model_name = "llama-3.3-70b-versatile"

llm = ChatGroq(model=model_name, api_key=test_api_key)


class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Query that is optimized web search.")
    justification: str = Field(
        None, description="Why this query is relevant to the user's request!"
    )


structured_llm = llm.with_structured_output(SearchQuery)

output = structured_llm.invoke("How does calcium CT score relate to high cholesterol?")

print(output)


def multiply(a: int, b: int) -> int:
    return a * b


llm_with_tools = llm.bind_tools([multiply])

msg = llm_with_tools.invoke("What is 2 times 3?")

print(msg.tool_calls)
