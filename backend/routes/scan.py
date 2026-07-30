
from fastapi import APIRouter, Depends, File, Query, UploadFile

from dependencies import get_medicine_service
from models.schemas import AlternativesResponse, CountryResult, ScanResponse
from services.medicine_service import MedicineService

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("/image", response_model=ScanResponse)
async def scan_image(
    file: UploadFile = File(...),
    destination_country: str | None = Query(default=None),
    service: MedicineService = Depends(get_medicine_service),
):
    image_bytes = await file.read()
    result = service.scan_image(image_bytes, destination_country)
    return ScanResponse(**result)


@router.get("/search", response_model=ScanResponse)
def search_medicine(
    medicine_name: str,
    destination_country: str | None = None,
    service: MedicineService = Depends(get_medicine_service),
):
    result = service.search_medicine(medicine_name, destination_country)
    return ScanResponse(**result)


@router.post("/alternatives", response_model=AlternativesResponse)
def get_alternatives(
    entry: CountryResult,
    medicine_name: str,
    service: MedicineService = Depends(get_medicine_service),
):
    result = service.get_alternatives(entry.model_dump(), medicine_name)
    return AlternativesResponse(**result)
