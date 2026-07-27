"""
OCRService — reads a medicine name out of a photo.

Responsibilities:
    - Own the image -> text extraction call (Gemini Vision).
    - Return a clean string, or None when nothing readable was found.

Explicitly NOT responsible for:
    - Looking up regulations for the extracted name (MedicineService).
    - Prompt formatting for anything other than this one OCR task.

Note on the old EasyOCR path (backend/ocr.py in the previous codebase):
Gemini Vision reads brand names and stylised packaging text far more
reliably than a general-purpose OCR engine, and it's already the model
used everywhere else in the app, so EasyOCR added a second dependency
and a second, worse code path for no benefit. It has been dropped.
"""
import io

from PIL import Image

from services.llm_service import LLMService
from utils.logger import get_logger

log = get_logger("services.ocr")

_PROMPT = """You are reading a photo of a medicine package or label.

Extract ONLY the medicine's brand or generic name exactly as printed.
Ignore dosage numbers, manufacturer logos, and barcodes.

If you cannot read a medicine name, respond with exactly: UNKNOWN

Respond with the medicine name only, nothing else."""


class OCRService:
    def __init__(self, llm: LLMService):
        self._llm = llm

    def read_medicine_name(self, image_bytes: bytes) -> str | None:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        name = self._llm.generate([image, _PROMPT])

        if not name or name.strip().upper() == "UNKNOWN":
            log.info("OCR did not detect a readable medicine name")
            return None

        return name.strip()
