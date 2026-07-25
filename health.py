from fastapi import APIRouter
from services.csv_services import get_dataframe

router = APIRouter()

df = get_dataframe()


@router.get("/health")
def health():

    return {
        "status": "healthy",
        "backend": "running",
        "dataset_loaded": not df.empty,
        "records": len(df)
    }