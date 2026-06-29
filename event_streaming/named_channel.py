from typing import TypedDict
from langgraph.stream import ProtocolEvent, StreamTransformer, StreamChannel


class ToolActivity(TypedDict):
    name: str
    status: str


class ToolActivityTransformer(StreamTransformer):
    required_stream_modes = ("tools",)

    def __init__(self, scope: tuple[str, ...] = ()) -> None:
        super().__init__(scope)
        self.activity = StreamChannel[ToolActivity]("tool_activity")

    def init(self) -> dict:
        return {"tool_activity": self.activity}

    def process(self, event: ProtocolEvent) -> ProtocolEvent:
        if event["method"] != "tools":
            return True
        data = event["params"]["data"]

        if isinstance(data, dict) and data.get("tool_name") and data.get("event"):
            status = "error" if data["event"] == "tool-error" else "started"

            self.activity.push({"name": data["tool_name"], "status": status})

        return True
