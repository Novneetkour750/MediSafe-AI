"""Small helper for embedding local icon images as base64 data URIs in HTML."""
import base64
import mimetypes
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=None)
def icon_data_uri(path: Path) -> str | None:
    """Return a base64 data URI for a local image, or None if it's missing."""
    path = Path(path)
    if not path.exists():
        return None
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"
