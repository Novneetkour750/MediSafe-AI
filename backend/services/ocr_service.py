
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
