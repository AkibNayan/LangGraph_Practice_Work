from langgraph.func import task, entrypoint
from langgraph.types import RetryPolicy, TimeoutPolicy


@task(timeout=TimeoutPolicy(idle_timeout=30), retry_policy=RetryPolicy(max_attempts=3))
async def call_api(url: str) -> str:
    """response = await fetch(url)
    return response.text"""
    pass


@entrypoint(timeout=60)
async def my_workflow(inputs: dict) -> str:
    result = await call_api("https://example.com")
    return result
