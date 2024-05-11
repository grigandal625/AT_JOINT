from pydantic import BaseModel


class ProcessTactModel:
    background: bool = False
    iterate: int = 1
    wait: int = 1000