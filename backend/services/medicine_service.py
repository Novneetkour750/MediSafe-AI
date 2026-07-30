
from services.llm_service import LLMService
from services.ocr_service import OCRService
from services.regulation_service import RegulationService
from services.search_service import SearchService
from utils.exceptions import MedicineNotDetectedError
from utils.logger import get_logger

log = get_logger("services.medicine")


def _row_block(d: dict) -> str:
    return (
        f"Medicine: {d.get('medicine_name', '')}\n"
        f"Brand: {d.get('brand_name', '')}\n"
        f"Generic: {d.get('generic_name', '')}\n"
        f"Country: {d.get('country', '')}\n"
        f"Status: {d.get('status', '')}\n"
        f"Regulation Type: {d.get('regulation_type', '')}\n"
        f"Authority: {d.get('authority', '')}\n"
        f"Reason: {d.get('reason', '')}\n"
        f"Alternatives: {d.get('alternatives', '')}\n"
        f"Traveller Advice: {d.get('traveller_advice', '')}\n"
        f"Source: {d.get('source', '')}\n"
        f"Last Updated: {d.get('last_updated', '')}"
    )


class MedicineService:
    def __init__(
        self,
        ocr: OCRService,
        search: SearchService,
        regulation: RegulationService,
        llm: LLMService,
    ):
        self._ocr = ocr
        self._search = search
        self._regulation = regulation
        self._llm = llm

    # -- Scan Medicine page -------------------------------------------------

    def scan_image(self, image_bytes: bytes, destination_country: str | None = None) -> dict:
        medicine_name = self._ocr.read_medicine_name(image_bytes)
        if not medicine_name:
            raise MedicineNotDetectedError("Could not read a medicine name from that photo.")

        results = self._regulation.get_country_results(medicine_name, destination_country)
        return {"medicine_name": medicine_name, "method": "ocr", "results": results}

    def search_medicine(self, medicine_name: str, destination_country: str | None = None) -> dict:
        results = self._regulation.get_country_results(medicine_name, destination_country)
        return {"medicine_name": medicine_name, "method": "manual_search", "results": results}

    def get_alternatives(self, entry: dict, medicine_name: str) -> dict:
        alternatives, source = self._regulation.resolve_alternatives(entry, medicine_name)
        return {"source": source, "alternatives": alternatives}

    # -- AI Chat page -------------------------

    def answer_chat_question(self, question: str) -> str:
        hits = self._search.search(question, k=5)
        context = "\n\n".join(_row_block(h["data"]) for h in hits)
        return self._llm.generate_chat_answer(question, context)

    def answer_followup_question(self, context: dict, question: str) -> str:
        """Powers "Know More": grounded in a specific card already shown
        to the user, no fresh search needed."""
        return self._llm.generate_followup_answer(context, question)
