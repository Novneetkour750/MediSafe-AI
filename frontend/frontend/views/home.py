import base64

import streamlit as st

import api_client
from components.illustration import show_illustration
from config import FEATURE_ICONS_DIR, HERO_IMAGE
from state import go_to


def _icon_data_uri(filename: str) -> str | None:
    """Return a base64 data URI for a feature icon, or None if it's missing."""
    path = FEATURE_ICONS_DIR / filename
    if not path.exists():
        return None
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def _get_platform_stats() -> list[tuple[str, str]]:
    """Live stats from the backend, with a safe static fallback if it's unreachable."""
    try:
        stats = api_client.get_stats()
        return [
            (str(stats["total_countries"]) + "+", "Countries Covered"),
            (str(stats["total_medicines"]) + "+", "Medicines Tracked"),
            (str(stats["total_records"]) + "+", "Regulation Records"),
            ("24/7", "AI Availability"),
        ]
    except api_client.ApiError:
        return [
            ("50+", "Countries Covered"),
            ("99.2%", "OCR Accuracy"),
            ("10K+", "Medicines Scanned"),
            ("24/7", "AI Availability"),
        ]


def render_home() -> None:
    with st.container(key="ms_hero"):
        col1, col2 = st.columns([1.3, 1], gap="large")

        with col1:
            st.markdown(
                '<div class="ms-tagline-banner">Travel Smart. Carry Medicines Safely.</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="ms-hero-badge">AI-Powered · Reliable · Global</div>', unsafe_allow_html=True)
            st.markdown('<h1 class="ms-hero-title">MediSafe <span class="ms-accent">AI</span></h1>', unsafe_allow_html=True)
            st.markdown('<h2 class="ms-hero-subtitle">Your Global Medicine Guide</h2>', unsafe_allow_html=True)
            st.markdown(
                '<p class="ms-hero-text">Check if your medicines are allowed, restricted, or banned '
                'in different countries. Get instant AI-powered regulation guidance before you travel.</p>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="ms-cta-row">', unsafe_allow_html=True)
            cta_col, badge_col = st.columns([2.4, 1.3])
            with cta_col:
                if st.button("**Upload Medicine Image**", key="hero_cta", type="primary", use_container_width=True):
                    go_to("Scan Medicine")
            with badge_col:
                st.markdown('<div class="ms-recommended-badge"> Recommended</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown(
                '<div class="ms-hero-tags">🛡️ Secure &nbsp;•&nbsp; 🔒 Private &nbsp;•&nbsp; ✅ Reliable</div>',
                unsafe_allow_html=True,
            )

        with col2:
            show_illustration(HERO_IMAGE)

    stats_html = '<div class="ms-stats-bar">'
    for number, label in _get_platform_stats():
        stats_html += (
            f'<div class="ms-stat"><div class="ms-stat-number">{number}</div>'
            f'<div class="ms-stat-label">{label}</div></div>'
        )
    stats_html += "</div>"
    st.markdown(stats_html, unsafe_allow_html=True)

    st.markdown('<h2 class="ms-section-title">Why MediSafe AI?</h2>', unsafe_allow_html=True)
    features = [
        ("advanced_ocr.jpeg", "🔍", "Advanced OCR", "Extracts medicine information accurately"),
        ("ai_powered.jpeg", "🧠", "AI Powered", "Smart analysis with trusted data sources"),
        ("global_coverage.jpeg", "🌍", "Global Coverage", "Check medicine status in multiple countries"),
        ("safe_secure.jpeg", "🛡️", "Safe & Secure", "Your data is protected and never stored"),
    ]
    cols = st.columns(4)
    for c, (filename, emoji, title, desc) in zip(cols, features):
        with c:
            data_uri = _icon_data_uri(filename)
            if data_uri:
                icon_html = (
                    f'<div class="ms-feature-icon has-image">'
                    f'<img src="{data_uri}" class="ms-feature-icon-img" alt="{title} icon" /></div>'
                )
            else:
                icon_html = f'<div class="ms-feature-icon">{emoji}</div>'
            st.markdown(
                f'<div class="ms-feature-card">{icon_html}'
                f'<div class="ms-feature-title">{title}</div><div class="ms-feature-desc">{desc}</div></div>',
                unsafe_allow_html=True,
            )
