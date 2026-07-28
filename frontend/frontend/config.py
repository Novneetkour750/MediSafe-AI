"""Frontend configuration: where the backend API lives, where assets are."""
import os
from pathlib import Path
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
CSS_FILE = BASE_DIR / "assets" / "css" / "style.css"
IMAGES_DIR = BASE_DIR / "assets" / "images"
HERO_IMAGE = IMAGES_DIR / "hero_illustration.png"
ABOUT_IMAGE = IMAGES_DIR / "about_illustration.png"
UPLOAD_ICON = IMAGES_DIR / "upload_cloud.png"
BOT_AVATAR = IMAGES_DIR / "bot_avatar.jpeg"
TECH_ICONS_DIR = IMAGES_DIR / "tech_icons"
FEATURE_ICONS_DIR = IMAGES_DIR / "feature_icons"
CLOCK_ICON = IMAGES_DIR / "icons" / "clock_icon.png"
HISTORY_FOLDER_ICON = IMAGES_DIR / "icons" / "history_folder.jpeg"
if "BACKEND_URL" in st.secrets:
  os.environ["BACKEND_URL"] = st.secrets["BACKEND_URL"]

