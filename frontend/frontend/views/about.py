import base64

import streamlit as st

from components.illustration import show_illustration
from config import ABOUT_IMAGE, TECH_ICONS_DIR


def _icon_data_uri(filename: str) -> str | None:
    path = TECH_ICONS_DIR / filename
    if not path.exists():
        return None
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def render_about() -> None:
    st.markdown('<h1 class="ms-page-title">ℹ️ About MediSafe AI</h1>', unsafe_allow_html=True)

    with st.container(key="ms_about_card"):
        col1, col2 = st.columns([1.6, 1], gap="large")

        with col1:
            st.markdown("#### About MediSafe AI")
            st.write(
                "MediSafe AI is an AI-powered platform that helps travelers check the legal status "
                "of their medicines across different countries. We aim to ensure safe and hassle-free "
                "travel by providing reliable and up-to-date information."
            )
            st.markdown("#### Our Mission")
            st.write(
                "To make global travel safer and easier by giving instant access to medicine "
                "regulations worldwide."
            )
            st.markdown("#### Our Vision")
            st.write(
                "A world where every traveler can check medicine regulations instantly, "
                "confidently, and without the risk of an unexpected customs issue."
            )

        with col2:
            show_illustration(ABOUT_IMAGE)

    st.markdown('<h2 class="ms-section-title">Technologies Used</h2>', unsafe_allow_html=True)
    techs = [
        ("fastapi.png", "🚀", "FastAPI"),
        ("streamlit.png", "🎈", "Streamlit"),
        ("python.png", "🐍", "Python"),
        ("gemini.png", "🧠", "Gemini AI"),
        ("faiss.png", "🔎", "FAISS"),
        ("sentence.jpeg", "🔢", "Sentence Transformers"),
    ]
    t_cols = st.columns(len(techs))
    for c, (filename, emoji, name) in zip(t_cols, techs):
        with c:
            data_uri = _icon_data_uri(filename) if filename else None
            if data_uri:
                icon_html = f'<img src="{data_uri}" class="ms-tech-icon" alt="{name} logo" />'
            else:
                icon_html = f'<span class="emoji">{emoji}</span>'
            st.markdown(f'<div class="ms-tech-pill">{icon_html}{name}</div>', unsafe_allow_html=True)

    st.markdown('<h2 class="ms-section-title">Our Journey</h2>', unsafe_allow_html=True)
    milestones = [
        ("💡", "Idea", "Identified the problem of unclear travel medicine regulations"),
        ("🛠️", "Build", "Built OCR-powered medicine detection for the hackathon"),
        ("🚀", "Launch", "Shipped the first working prototype of MediSafe AI"),
        ("🏗️", "Rebuild", "Refactored into a clean FastAPI backend + Streamlit frontend"),
    ]
    tl_cols = st.columns(len(milestones))
    for c, (icon, title, desc) in zip(tl_cols, milestones):
        with c:
            st.markdown(
                f'<div class="ms-timeline-node"><div class="ms-timeline-icon">{icon}</div>'
                f'<div class="ms-timeline-title">{title}</div><div class="ms-timeline-desc">{desc}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<h2 class="ms-section-title">Key Capabilities</h2>', unsafe_allow_html=True)
    capabilities = [
        ("🔍", "OCR Medicine Detection", "Reads medicine names directly from a photo"),
        ("🌍", "Country Regulation Lookup", "Live status for 50+ countries from our regulation database"),
        ("🤖", "AI Travel Assistant", "Conversational guidance grounded in real regulation data"),
    ]
    cap_cols = st.columns(3)
    for c, (icon, title, desc) in zip(cap_cols, capabilities):
        with c:
            st.markdown(
                f'<div class="ms-feature-card"><div class="ms-feature-icon">{icon}</div>'
                f'<div class="ms-feature-title">{title}</div><div class="ms-feature-desc">{desc}</div></div>',
                unsafe_allow_html=True,
            )
