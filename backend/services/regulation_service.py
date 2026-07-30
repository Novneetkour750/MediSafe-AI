
import re

from config import get_settings
from services.search_service import SearchService
from utils.logger import get_logger

log = get_logger("services.regulation")

_COUNTRY_FLAGS = {
    "United States": "🇺🇸", "USA": "🇺🇸",
    "United Kingdom": "🇬🇧", "UK": "🇬🇧",
    "India": "🇮🇳",
    "United Arab Emirates": "🇦🇪", "UAE": "🇦🇪",
    "Canada": "🇨🇦",
    "Australia": "🇦🇺",
    "Germany": "🇩🇪",
    "France": "🇫🇷",
    "Japan": "🇯🇵",
    "Singapore": "🇸🇬",
    "China": "🇨🇳",
}

_RESTRICTED_KEYWORDS = ("restrict", "ban", "prescription")


def _split_alternative_text(raw: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;,/]| and ", raw) if p.strip()]


class RegulationService:
    def __init__(self, search_service: SearchService):
        self._search = search_service
        self._min_score = get_settings().min_match_score

    def get_country_results(self, query: str, destination_country: str | None = None, k: int | None = None) -> list[dict]:
        """One result per country, max — never two cards for the same
        country. Searches a wide candidate pool (not just `k` rows) so
        that every country in the dataset gets a fair chance to be
        considered, then keeps only each country's single best-scoring
        match before capping to `k`."""
        if k is None:
            k = get_settings().default_top_k

        search_pool_size = max(k * 15, 100)
        hits = self._search.search(query, destination_country=destination_country, k=search_pool_size)

        best_by_country: dict[str, dict] = {}
        for hit in hits:
            if hit["score"] < self._min_score:
                continue

            data = hit["data"]
            country = (data.get("country") or "").strip()
            if not country:
                continue
            if destination_country and country.lower() != destination_country.strip().lower():
                continue

            key = country.lower()
            if key not in best_by_country or hit["score"] > best_by_country[key]["score"]:
                best_by_country[key] = {"score": hit["score"], "data": data}

        ordered = sorted(best_by_country.values(), key=lambda r: -r["score"])[:k]

        return [
            {
                "flag": _COUNTRY_FLAGS.get(entry["data"].get("country", ""), ""),
                "country": entry["data"].get("country", ""),
                "status": entry["data"].get("status", ""),
                "reason": entry["data"].get("reason", ""),
                "travel_advice": entry["data"].get("traveller_advice", ""),
                "alternative": entry["data"].get("alternatives", ""),
                "confidence": max(40, min(98, round(entry["score"] * 100))),
                "medicine_name": entry["data"].get("medicine_name", "") or query,
            }
            for entry in ordered
        ]

    def is_restricted_status(self, status: str) -> bool:
        return any(k in (status or "").lower() for k in _RESTRICTED_KEYWORDS)

    def resolve_alternatives(self, entry: dict, medicine_name: str) -> tuple[list[dict], str]:
        """Grounded alternative lookup — never invents a substitute.
        1. Use the CSV's own `alternative` text for this row if present.
        2. Otherwise fall back to other medicines marked "Allowed" in
           the same destination country."""
        country = entry.get("country", "")
        raw = (entry.get("alternative") or "").strip()

        if raw:
            names = _split_alternative_text(raw)
            if names:
                return (
                    [{"name": n, "generic_name": "", "reason": "", "source": ""} for n in names],
                    "database",
                )

        return self._find_allowed_alternatives(medicine_name, country, entry.get("reason", "")), "search"

    def _find_allowed_alternatives(self, medicine_name: str, destination_country: str, reason: str = "", k: int = 5) -> list[dict]:
        if not destination_country or not medicine_name:
            return []

        query = f"medicine similar to {medicine_name}"
        if reason:
            query += f" used for {reason}"

        hits = self._search.search(query, destination_country=destination_country, k=max(k * 6, 30))

        destination_lower = destination_country.strip().lower()
        medicine_lower = medicine_name.strip().lower()
        seen: set[str] = set()
        alternatives = []

        for hit in hits:
            data = hit["data"]
            if (data.get("country") or "").strip().lower() != destination_lower:
                continue
            if "allow" not in (data.get("status") or "").lower():
                continue

            name = (data.get("medicine_name") or data.get("brand_name") or "").strip()
            if not name or name.lower() == medicine_lower or name.lower() in seen:
                continue
            seen.add(name.lower())

            alternatives.append({
                "name": name,
                "generic_name": data.get("generic_name", ""),
                "reason": data.get("reason", ""),
                "source": data.get("source", ""),
            })
            if len(alternatives) >= k:
                break

        return alternatives
