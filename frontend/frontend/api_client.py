import requests

from config import BACKEND_URL


class ApiError(Exception):
  def _request(method: str, path: str, **kwargs):
    try:
        response = requests.request(method, f"{BACKEND_URL}{path}", timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        raise ApiError(str(exc)) from exc


def scan_image(file_bytes: bytes, filename: str, destination_country: str | None) -> dict:
    files = {"file": (filename, file_bytes)}
    params = {"destination_country": destination_country} if destination_country else {}
    return _request("POST", "/api/scan/image", files=files, params=params)


def search_medicine(medicine_name: str, destination_country: str | None) -> dict:
    params = {"medicine_name": medicine_name}
    if destination_country:
        params["destination_country"] = destination_country
    return _request("GET", "/api/scan/search", params=params)


def get_alternatives(entry: dict, medicine_name: str) -> dict:
    return _request(
        "POST", "/api/scan/alternatives",
        params={"medicine_name": medicine_name},
        json=entry,
    )


def chat(question: str) -> str:
    return _request("POST", "/api/chat", json={"question": question})["reply"]


def chat_followup(question: str, context: dict) -> str:
    return _request(
        "POST", "/api/chat/followup",
        json={"question": question, "context": context},
    )["reply"]


def get_countries() -> list[str]:
    return _request("GET", "/api/countries")["countries"]


def get_stats() -> dict:
    return _request("GET", "/api/stats")
