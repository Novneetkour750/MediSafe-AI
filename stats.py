from fastapi import APIRouter
from services.csv_services import get_dataframe

router = APIRouter()

df = get_dataframe()


@router.get("/stats")
def get_stats():

    return {
        "total_records": len(df),
        "total_medicines": df["medicine_name"].nunique(),
        "total_countries": df["country"].nunique(),
        "allowed": len(df[df["status"].str.lower() == "allowed"]),
        "restricted": len(df[df["status"].str.lower() == "restricted"]),
        "banned": len(df[df["status"].str.lower() == "banned"]),
        "authorities": df["authority"].nunique()
    }