from fastapi import APIRouter
from services.csv_services import get_dataframe

router = APIRouter()

df = get_dataframe()

@router.get("/medicines")
def get_medicines():
    medicines = sorted(df["medicine_name"].dropna().unique().tolist())
    return {"medicines": medicines}