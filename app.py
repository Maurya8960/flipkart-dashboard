import streamlit as st
import pandas as pd
import numpy as np
import json
import time

# 1. Browser Tab (Window) me Flipkart ka logo (favicon)
st.set_page_config(
    page_title="Flipkart Ops Hub",
    page_icon="https://img1a.flixcart.com/www/promos/new/20150528-140547-favicon-retina.ico",
    layout="wide"
)

# ==========================================
# 1. macOS GLASSMORPHISM CSS INJECTION
# ==========================================
glass_css = """
<style>
/* Background gradient */
.stApp {
    background: radial-gradient(circle at 15% 20%, #1a1e2e 0%, #0d0f18 100%) !important;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", sans-serif;
}

/* Glass Cards for Metrics */
div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.04) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 16px 20px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
}

/* Glass Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(18, 22, 34, 0.6) !important;
    backdrop-filter: blur(25px) !important;
    -webkit-backdrop-filter: blur(25px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}

/* Glass Tabs Container */
div[data-baseweb="tab-list"] {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(16px) !important;
    border-radius: 14px !important;
    padding: 4px !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
}

/* Glass Buttons */
button[kind="primary"], div.stButton > button {
    background: rgba(255, 255, 255, 0.07) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 10px !important;
    color: #f8fafc !important;
    transition: all 0.25s ease !important;
}

button[kind="primary"]:hover, div.stButton > button:hover {
    background: rgba(255, 255, 255, 0.15) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
}

/* macOS Window Bar Simulation */
.mac-window-bar {
    display: flex;
    gap: 8px;
    padding-bottom: 12px;
}
.mac-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
}
.dot-red { background: #ff5f56; }
.dot-yellow { background: #ffbd2e; }
.dot-green { background: #27c93f; }
</style>
"""
st.markdown(glass_css, unsafe_allow_html=True)

# ==========================================
# 2. LOGIN AUTHENTICATION
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password"] == "admin123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("""
        <div class="mac-window-bar">
            <span class="mac-dot dot-red"></span>
            <span class="mac-dot dot-yellow"></span>
            <span class="mac-dot dot-green"></span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("### 🔒 Ops Hub Authentication")
        st.text_input("Enter Keycard Passcode (hint: admin123)", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("### 🔒 Ops Hub Authentication")
        st.text_input("Enter Keycard Passcode (hint: admin123)", type="password", on_change=password_entered, key="password")
        st.error("Invalid credentials.")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 3. macOS HEADER & DATA ENGINE
# ==========================================
st.markdown("""
<div class="mac-window-bar">
    <span class="mac-dot dot-red"></span>
    <span class="mac-dot dot-yellow"></span>
    <span class="mac-dot dot-green"></span>
</div>
""", unsafe_allow_html=True)

# 2. Main Window me Flipkart ka Custom Header
st.markdown("""
<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
    <img src="https://logos-world.net/wp-content/uploads/2020/11/Flipkart-Icon.png" alt="Flipkart Logo" height="45">
    <h1 style="margin: 0; padding: 0; font-size: 2.2rem;">Flipkart Operations & Triage Hub</h1>
</div>
""", unsafe_allow_html=True)
st.caption("macOS Frosted Glass Terminal • Production Intelligence Engine")
