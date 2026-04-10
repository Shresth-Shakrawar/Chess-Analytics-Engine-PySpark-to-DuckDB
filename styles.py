import streamlit as st
import altair as alt

def apply_custom_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    /* ── Base ── */
    html, body, [class*="css"], .stApp {
        font-family: 'DM Sans', sans-serif !important;
        background-color: #0A0A0A !important;
        color: #E0E0E0 !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #0F0F0F !important;
        border-right: 1px solid #1A1A1A !important;
    }
    [data-testid="stSidebar"] * {
        color: #AAAAAA !important;
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] .stSlider label p {
        color: #E0E0E0 !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }

    /* ── Typography & Layout ── */
    h1, h2, h3 { font-weight: 600 !important; color: #FFFFFF !important; }
    hr { border-top: 1px solid #1A1A1A !important; margin: 2rem 0 !important; }

    /* ── KPIs ── */
    [data-testid="metric-container"] {
        background-color: #111111;
        border: 1px solid #1E1E1E;
        border-radius: 8px;
        padding: 20px;
    }
    [data-testid="stMetricValue"] {
        font-family: 'DM Mono', monospace !important;
        font-size: 2rem !important;
        color: #FFFFFF !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
    }
    [data-testid="stMetricDelta"] { display: none; }

    /* ── UI Elements ── */
    [data-testid="stSelectbox"] > div > div {
        background-color: #111111 !important;
        border-color: #2A2A2A !important;
    }
    #MainMenu, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

def register_theme():
    @alt.theme.register("chess_clean", enable=True)
    def chess_clean_theme():
        return alt.theme.ThemeConfig({
            "config": {
                "background": "transparent",
                "title": {"font": "DM Sans", "fontSize": 13, "fontWeight": 600, "color": "#A0A0A0", "anchor": "start"},
                "axis": {
                    "labelFont": "DM Mono", "titleFont": "DM Sans",
                    "labelColor": "#555555", "titleColor": "#888888",
                    "gridColor": "#1E1E1E", "domainColor": "#2A2A2A",
                    "tickColor": "#2A2A2A"
                },
                "legend": {
                    "labelFont": "DM Sans", "titleFont": "DM Sans",
                    "labelColor": "#AAAAAA", "titleColor": "#888888",
                },
                "view": {"stroke": "transparent"}
            }
        })
    alt.themes.enable("chess_clean")