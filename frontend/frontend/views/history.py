import streamlit as st

from components.icons import icon_data_uri
from config import CLOCK_ICON, HISTORY_FOLDER_ICON

_CLOCK_URI = icon_data_uri(CLOCK_ICON)
_FOLDER_URI = icon_data_uri(HISTORY_FOLDER_ICON)
_CLOCK_IMG = f'<img src="{_CLOCK_URI}" class="ms-icon-img ms-icon-clock" alt="">' if _CLOCK_URI else "🕓"
_FOLDER_IMG = f'<img src="{_FOLDER_URI}" class="ms-icon-img ms-icon-folder" alt="">' if _FOLDER_URI else "🗂️"


def _render_empty_state(emoji: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="ms-card ms-empty-state">
            <div class="emoji">{emoji}</div>
            <div><strong>{title}</strong></div>
            <div>{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_history() -> None:
    st.markdown(f'<h1 class="ms-page-title">{_CLOCK_IMG} History</h1>', unsafe_allow_html=True)
    st.markdown('<p class="ms-page-subtitle">Your previous medicine searches and scans</p>', unsafe_allow_html=True)

    if not st.session_state.history:
        _render_empty_state(_FOLDER_IMG, "No history yet", "Analyze a medicine on the Scan Medicine page to see it here.")
        return

    st.markdown('<div class="ms-history-filters">', unsafe_allow_html=True)
    search_col, filter_col = st.columns([2.2, 1])
    with search_col:
        search_term = st.text_input(
            "🔎 Search history", placeholder="Search by medicine name...", label_visibility="collapsed"
        )
    with filter_col:
        method_options = ["All Methods"] + sorted({entry["method"] for entry in st.session_state.history})
        method_filter = st.selectbox("Filter by method", method_options, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    filtered = [
        entry for entry in reversed(st.session_state.history)
        if (search_term.lower() in entry["name"].lower() if search_term else True)
        and (method_filter == "All Methods" or entry["method"] == method_filter)
    ]

    if not filtered:
        _render_empty_state("🔍", "No matching results", "Try a different search term or filter.")
        return

    for entry in filtered:
        st.markdown(
            f"""
            <div class="ms-history-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div class="ms-history-name">💊 {entry['name']}</div>
                    <div class="ms-history-tag">{entry['method']}</div>
                </div>
                <div class="ms-history-meta">{_CLOCK_IMG} {entry['time']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("📄 View Details"):
            for line in entry["details"]:
                st.write(f"• {line}")
