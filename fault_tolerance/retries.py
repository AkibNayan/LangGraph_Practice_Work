from langgraph.types import RetryPolicy, default_retry_on

"""builder.add_node("call_api", call_api, retry_policy=RetryPolicy(max_attempts=3))"""
"""
def custom_retry_on(exc: BaseException) -> bool:
    if isinstance(exc, MyCustomError):
        return False
    return default_retry_on(exc)

builder.add_node("call_api", call_api, retry_policy=RetryPolicy(max_attempts=3, retry_on=custom_retry_on))
"""

