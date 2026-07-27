import streamlit as st

from components.navbar import LOGO_MARK_SVG


def render_footer() -> None:
    st.markdown(
        f"""
        <div class="ms-site-footer">
            <div class="ms-site-footer-top">
                <div class="ms-site-footer-brand">{LOGO_MARK_SVG} MediSafe <span class="ms-logo-accent">AI</span></div>
                <div class="ms-site-footer-tagline">Built for AI Hackathon</div>
            </div>
            <div class="ms-site-footer-links">
                <a href="#" class="ms-footer-link">Privacy</a>
                <span class="ms-footer-dot">•</span>
                <a href="#" class="ms-footer-link">Contact</a>
                <span class="ms-footer-dot">•</span>
                <a href="#" class="ms-footer-link">GitHub</a>
            </div>
            <div class="ms-site-footer-copy">© 2026 MediSafe AI. All rights reserved.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
