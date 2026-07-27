"""
Read-only reference data used to populate dropdowns and the platform
stats bar. Deliberately separate from /scan and /chat since it has a
different shape (no service orchestration needed — straight repository reads).
"""
from fastapi import APIRouter, Depends

from database.regulation_repository import RegulationRepository, get_repository
from models.schemas import CountriesResponse, MedicinesResponse, StatsResponse

router = APIRouter(prefix="/api", tags=["reference"])


@router.get("/countries", response_model=CountriesResponse)
def get_countries(repo: RegulationRepository = Depends(get_repository)):
    return CountriesResponse(countries=repo.list_countries())


@router.get("/medicines", response_model=MedicinesResponse)
def get_medicines(repo: RegulationRepository = Depends(get_repository)):
    return MedicinesResponse(medicines=repo.list_medicines())


@router.get("/stats", response_model=StatsResponse)
def get_stats(repo: RegulationRepository = Depends(get_repository)):
    return StatsResponse(**repo.summary_stats())
