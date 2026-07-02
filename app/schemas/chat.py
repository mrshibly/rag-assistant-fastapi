from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    sources: list[str] | None = None
    tool_used: str | None = None


class IngestResponse(BaseModel):
    filename: str
    chunks: int
