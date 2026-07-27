"""
Domain-specific exceptions.

Routes catch these (via the FastAPI exception handlers registered in
app.py) and translate them into proper HTTP status codes. Services
raise them instead of returning ad-hoc {"success": False, ...} dicts,
so error handling is consistent everywhere.
"""


class MediSafeError(Exception):
    """Base class for all application errors."""
    status_code = 500


class MedicineNotDetectedError(MediSafeError):
    """OCR ran successfully but no medicine name could be read from the image."""
    status_code = 422


class NoRegulationDataError(MediSafeError):
    """The regulation dataset has no matching entry for the query."""
    status_code = 404


class LLMGenerationError(MediSafeError):
    """The LLM call failed or returned something unusable."""
    status_code = 502
