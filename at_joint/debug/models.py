from pydantic import BaseModel


class ProcessTactModel(BaseModel):
    background: bool = True
    iterate: int = 1
    wait: int = 1000