"""All st.session_state initialization in one place, so every view can
assume the keys it needs already exist."""
import streamlit as st


def init_session_state() -> None:
    defaults = {
        "page": "Home",
        "history": [],
        "chat_messages": [
            {
                "role": "assistant",
                "text": (
                    "👋 Hi! I'm your MediSafe AI Assistant. "
                    "Ask me anything about medicines and travel regulations."
                ),
            }
        ],
        "chat_context": None,
        "chat_autoquery": None,
        "expanded_alternatives": set(),
        "scan_mode": "text",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to(page: str) -> None:
    st.session_state.page = page
    st.rerun()
