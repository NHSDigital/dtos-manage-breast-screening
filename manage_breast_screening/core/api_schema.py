from ninja import Schema


class StatusResponse(Schema):
    status: str


class ErrorResponse(Schema):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str | None = None
