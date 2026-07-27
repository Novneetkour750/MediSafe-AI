import streamlit as st

from components.icons import icon_data_uri
from config import CLOCK_ICON
from state import go_to

_CLOCK_URI = icon_data_uri(CLOCK_ICON)

LOGO_MARK_SVG = (
    '<svg class="ms-logo-mark" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" '
    'role="img" aria-label="MediSafe AI logo">'
    '<defs><linearGradient id="msLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
    '<stop offset="0%" stop-color="#2F6FED"/><stop offset="100%" stop-color="#16A34A"/>'
    '</linearGradient></defs>'
    '<circle cx="20" cy="20" r="19" fill="url(#msLogoGrad)"/>'
    '<path d="M20 11v18M11 20h18" stroke="#FFFFFF" stroke-width="4.5" stroke-linecap="round"/>'
    '</svg>'
)


def render_navbar() -> None:
    if _CLOCK_URI:
        st.markdown(
            f"""
            <style>
            .st-key-nav_history button p {{
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            .st-key-nav_history button p::before {{
                content: "";
                display: inline-block;
                width: 1.05em;
                height: 1.05em;
                background-image: url('{_CLOCK_URI}');
                background-size: contain;
                background-repeat: no-repeat;
                background-position: center;
                flex-shrink: 0;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    nav_cols = st.columns([2.4, 1, 1.3, 1, 1, 1.3])

    with nav_cols[0]:
        st.markdown(
            f'<div class="ms-logo">{LOGO_MARK_SVG} <span>MediSafe</span> '
            '<span class="ms-logo-accent">AI</span></div>',
            unsafe_allow_html=True,
        )

    for col, label in zip(nav_cols[1:5], ["Home", "Scan Medicine", "AI Chat", "About"]):
        with col:
            btn_type = "primary" if st.session_state.page == label else "secondary"
            if st.button(label, key=f"nav_{label}", use_container_width=True, type=btn_type):
                go_to(label)

    with nav_cols[5]:
        btn_type = "primary" if st.session_state.page == "History" else "secondary"
        label = "History" if _CLOCK_URI else "🕓 History"
        if st.button(label, key="nav_history", use_container_width=True, type=btn_type):
            go_to("History")
