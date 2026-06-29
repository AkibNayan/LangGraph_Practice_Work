from langgraph.stream import ProtocolEvent, StreamTransformer


class MyTransformer(StreamTransformer):
    def init(self) -> dict: ...

    def process(self, event: ProtocolEvent) -> ProtocolEvent: ...

    def finalize(self) -> None: ...

    def fail(self, err: BaseException) -> None: ...


class CustomTransformer(StreamTransformer):
    required_stream_modes = ("custom",)

    def process(self, event: ProtocolEvent) -> ProtocolEvent:
        if event["method"] == "custom":
            ...
        return True
