from fastapi import APIRouter, Depends

from database.regulation_repository import RegulationRepository, get_repository
from models.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(repo: RegulationRepository = Depends(get_repository)):
    records = len(repo.dataframe)
    return HealthResponse(status="healthy", dataset_loaded=records > 0, records=records)
