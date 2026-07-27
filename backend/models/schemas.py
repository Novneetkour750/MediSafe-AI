"""
API contracts. Routes validate against these; services return plain
dataclasses/dicts that routes adapt into these before responding.
Keeping schemas separate from services means the API shape can evolve
without touching business logic, and vice versa.
"""
from pydantic import BaseModel, Field


class CountryResult(BaseModel):
    flag: str = ""
    country: str
    status: str
    reason: str = ""
    travel_advice: str = ""
    alternative: str = ""
    confidence: int = Field(ge=0, le=100)
    medicine_name: str


class ScanResponse(BaseModel):
    medicine_name: str
    method: str  # "ocr" | "manual_search"
    results: list[CountryResult]


class AlternativeItem(BaseModel):
    name: str
    generic_name: str = ""
    reason: str = ""
    source: str = ""


class AlternativesResponse(BaseModel):
    source: str  # "database" | "search"
    alternatives: list[AlternativeItem]


class ChatRequest(BaseModel):
    question: str


class ChatContext(BaseModel):
    medicine_name: str | None = None
    country: str | None = None
    status: str | None = None
    reason: str | None = None
    travel_advice: str | None = None
    alternative: str | None = None


class FollowUpRequest(BaseModel):
    question: str
    context: ChatContext


class ChatResponse(BaseModel):
    reply: str


class CountriesResponse(BaseModel):
    countries: list[str]


class MedicinesResponse(BaseModel):
    medicines: list[str]


class StatsResponse(BaseModel):
    total_records: int
    total_medicines: int
    total_countries: int
    allowed: int
    restricted: int
    banned: int
    authorities: int


class HealthResponse(BaseModel):
    status: str
    dataset_loaded: bool
    records: int
