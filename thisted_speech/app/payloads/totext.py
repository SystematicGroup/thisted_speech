from pydantic import BaseModel


class ToTextResult(BaseModel):
    is_final: bool
    transcript: str

class StopPayload(BaseModel):
    user_name: str
