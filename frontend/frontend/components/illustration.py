import streamlit as st


def show_illustration(image_path, use_container_width: bool = True) -> None:
    """Render an illustration if the file exists; otherwise fall back to an
    emoji so the layout never breaks or shows a broken-image icon."""
    if image_path.exists():
        st.image(str(image_path), use_container_width=use_container_width)
    else:
        st.markdown('<div style="font-size:4rem;text-align:center;">💊🌍🛡️</div>', unsafe_allow_html=True)
