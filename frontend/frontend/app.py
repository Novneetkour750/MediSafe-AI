import streamlit as st

from components.footer import render_footer
from components.navbar import render_navbar
from config import CSS_FILE,FAVICON_IMAGE
from state import init_session_state
from views.about import render_about
from views.chat import render_chat
from views.history import render_history
from views.home import render_home
from views.scan import render_scan


st.set_page_config(
    page_title="MediSafe AI",
    page_icon=str(FAVICON_IMAGE), 
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    #MainMenu {display: none;}
    footer {display: none;}
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
    }
    [data-testid="stSidebar"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    [data-testid="stDecoration"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stStatusWidget"] {display: none;}
    [data-testid="stAppViewContainer"] {padding-top: 0 !important;}
    [data-testid="stAppViewContainer"] > .main {padding-top: 0 !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

if CSS_FILE.exists():
    st.markdown(f"<style>{CSS_FILE.read_text()}</style>", unsafe_allow_html=True)

init_session_state()

PAGES = {
    "Home": render_home,
    "Scan Medicine": render_scan,
    "AI Chat": render_chat,
    "About": render_about,
    "History": render_history,
}

render_navbar()
PAGES[st.session_state.page]()
render_footer()
