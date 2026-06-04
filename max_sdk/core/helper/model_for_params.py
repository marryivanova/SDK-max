from pydantic import BaseModel, Field


class ApiConfig(BaseModel):
    base_url: str
    access_token: str
    timeout: float = Field(default=30.0, gt=0)
    connect_timeout: float = Field(default=10.0, gt=0)
