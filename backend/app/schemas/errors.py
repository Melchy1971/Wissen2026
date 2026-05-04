from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiErrorBody(BaseModel):
    model_config = ConfigDict(strict=True)

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    error: ApiErrorBody
