from fastapi import APIRouter
from services.csv_services import get_dataframe

router = APIRouter()

df = get_dataframe()

@router.get("/countries")
def get_countries():
    countries = sorted(df["country"].dropna().unique().tolist())
    return {"countries": countries}