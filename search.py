from fastapi import APIRouter
from services.csv_services import get_dataframe

router = APIRouter()

df = get_dataframe()


@router.get("/search")
def search_medicine(medicine: str, country: str):

    result = df[
        (df["medicine_name"].str.lower() == medicine.lower()) &
        (df["country"].str.lower() == country.lower())
    ]

    if result.empty:
        return {"message": "Medicine not found"}

    return result.to_dict(orient="records")