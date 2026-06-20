from langgraph.func import entrypoint, task
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

prompt_api = os.getenv("test_api_key")

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=prompt_api)


@task
def generate_joke(topic: str):
    """Fist LLM call to generate initial joke."""
    msg = llm.invoke(f"Write a short joke about: {topic}")

    return msg.content


def check_punchline(joke: str):
    """Gate function to check if the joke has a punchline."""
    # Simple check - does the joke contain '?' or '!'
    if "?" in joke or "!" in joke:
        return "Fail"
    else:
        return "Pass"


@task
def improve_joke(joke: str):
    """Second LLM call to improve the joke."""
    msg = llm.invoke(f"Make this joke funnier by adding wordplay: {joke}")

    return msg.content


@task
def polish_joke(joke: str):
    """Third LLM call to polish the joke."""
    msg = llm.invoke(f"Add a surprising twist to this joke: {joke}")

    return msg.content


@entrypoint
def prompt_chaining_workflow(topic: str):
    original_joke = generate_joke(topic).result()
    if check_punchline(original_joke) == "Pass":
        return original_joke

    improved_joke = improve_joke(original_joke).result()

    return polish_joke(improved_joke).result()


# Invoke
result = prompt_chaining_workflow("cats")

print(result)
