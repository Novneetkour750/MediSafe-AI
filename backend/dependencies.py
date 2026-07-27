"""
Composition root. Builds every service exactly once and exposes
FastAPI dependency functions for routes to depend on.

Routes never construct a service themselves — they declare
`service: MedicineService = Depends(get_medicine_service)` and FastAPI
(via this module) hands them the shared singleton. This is what makes
routes testable: swap a dependency override in tests, no import-time
side effects to fight with.
"""
from functools import lru_cache

from config import get_settings
from database.regulation_repository import get_repository
from services.llm_service import LLMService
from services.medicine_service import MedicineService
from services.ocr_service import OCRService
from services.regulation_service import RegulationService
from services.search_service import get_search_service


@lru_cache
def _build_llm_service() -> LLMService:
    settings = get_settings()
    return LLMService(api_key=settings.gemini_api_key, model_name=settings.gemini_model)


@lru_cache
def _build_medicine_service() -> MedicineService:
    get_repository()  # ensure dataset is loaded before anything else touches it
    search = get_search_service()
    llm = _build_llm_service()
    return MedicineService(
        ocr=OCRService(llm),
        search=search,
        regulation=RegulationService(search),
        llm=llm,
    )


def get_medicine_service() -> MedicineService:
    return _build_medicine_service()
