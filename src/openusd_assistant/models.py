from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AnswerStatus = Literal["answer", "insufficient_context"]


class Chunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    path: str
    title: str
    start_line: int
    end_line: int
    text: str
    url: str


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=2_000)


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    chunk_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class DraftAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: AnswerStatus
    answer: str = ""
    evidence: list[Evidence] = Field(default_factory=list)


class Source(BaseModel):
    chunk_id: str
    path: str
    title: str
    start_line: int
    end_line: int
    url: str
    quote: str


class AskResponse(BaseModel):
    status: AnswerStatus
    answer: str
    sources: list[Source] = Field(default_factory=list)


class AssistantError(Exception):
    status_code = 500
    detail = "The assistant could not complete the request."


class InvalidModelOutput(AssistantError):
    status_code = 502
    detail = "The model returned an invalid answer or unsupported citations."


class DependencyUnavailable(AssistantError):
    status_code = 503
    detail = "The index or a model provider is unavailable."


class DependencyTimeout(AssistantError):
    status_code = 504
    detail = "A model provider or the index timed out."
