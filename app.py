import streamlit as st
import altair as alt
from styles import apply_custom_style, register_theme

from pipeline.queries import (
    get_kpis, get_opening_efficacy, get_draw_rate_trend,
    get_popular_openings, get_opening_win_rate_by_elo,
    get_elo_distribution
)

# ── SETUP ──────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Chess Analytics", page_icon="♟", layout="wide")
apply_custom_style()
register_theme()

# ── CONSTANTS (NEON THEME) ─────────────────────────────────────────────────────
NEON_CYAN   = '#00E5FF'  # Bright electric cyan
NEON_PINK   = '#FF007F'  # Hot neon pink
NEON_PURPLE = '#B026FF'  # Vibrant purple
WHITE       = '#FFFFFF'  # Pure white for high-contrast accents

# Updated global scale for Win/Draw/Loss across all tabs
RESULT_SCALE = alt.Scale(
    domain=['White Win', 'Draw', 'Black Win'], 
    range=[NEON_CYAN, NEON_PURPLE, NEON_PINK]
)

def render_header(title, subtitle=""):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Filters")
    min_elo, max_elo = st.slider("Elo Range", 800, 2800, (1400, 2000), 50)
    st.caption("Some charts show data across all ratings regardless of this filter.")

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.title("Chess Analytics")
st.markdown("*Lichess Open Database — Patterns, openings, and outcomes across millions of games*")

# ── DATA FETCHING & KPIs ───────────────────────────────────────────────────────
kpis = get_kpis(min_elo, max_elo)

# 1. Filtered openings for the KPI metric
filtered_openings = get_popular_openings(min_elo, max_elo)
top_opening = filtered_openings[0] if filtered_openings else "N/A"

# 2. Global openings for the Deep Dive Tab (spanning the whole 800-2800 range)
global_openings = get_popular_openings(800, 2800)

cols = st.columns(5)
metrics = [
    ("Games Analyzed", f"{kpis['total_games']:,}"),
    ("White Wins", f"{kpis['white_win_rate']:.1f}%"),
    ("Draws", f"{kpis['draw_rate']:.1f}%"),
    ("Average Rating", f"{kpis['avg_elo']:,}"),
    ("Top Opening", top_opening) 
]

for col, (label, val) in zip(cols, metrics):
    col.metric(label, val)

st.divider()

# ── DASHBOARD BODY (TABS) ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎯 Openings", "📊 Ratings & Skill", "🔍 Deep Dive"])

# TAB 1: Openings
with tab1:
    # --- ROW 1: Opening Outcomes ---
    render_header("Opening Outcomes", "Which openings favor White, Black, or end in draws?")
    efficacy_df = get_opening_efficacy(min_elo, max_elo)
    
    efficacy_chart = alt.Chart(efficacy_df.to_pandas()).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X('sum(count):Q', stack="normalize", axis=alt.Axis(format='%', title=None)),
        y=alt.Y('BaseOpening:N', sort='-x', title=None),
        color=alt.Color('ResultLabel:N', scale=RESULT_SCALE, legend=alt.Legend(title=None, orient="top")),
        tooltip=['BaseOpening', 'ResultLabel', alt.Tooltip('count', format=',')]
    ).properties(height=400)
    st.altair_chart(efficacy_chart, width="stretch")

    st.divider() 

    # --- ROW 2: Most Played Openings ---
    render_header("Most Played Openings", "The sheer volume of games played by opening choice")
    
    volume_chart = alt.Chart(efficacy_df.to_pandas()).mark_bar(color=NEON_CYAN, cornerRadiusEnd=3).encode(
        x=alt.X('sum(count):Q', title="Total Games Played"),
        y=alt.Y('BaseOpening:N', sort='-x', title=None),
        tooltip=['BaseOpening', alt.Tooltip('sum(count):Q', title='Total Games', format=',')]
    ).properties(height=400)
    st.altair_chart(volume_chart, width="stretch")

# TAB 2: Ratings
with tab2:
    # --- ROW 1: Rating Distribution ---
    render_header("Rating Distribution", "Where most players fall on the rating spectrum")
    elo_dist_df = get_elo_distribution(min_elo, max_elo)
    
    elo_dist_chart = alt.Chart(elo_dist_df.to_pandas()).mark_bar(opacity=0.85).encode(
        x=alt.X('EloBucket:O', title="Rating Bracket", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('PlayerCount:Q', title="Number of Players"),
        color=alt.Color('Side:N', scale=alt.Scale(domain=['White', 'Black'], range=[NEON_CYAN, NEON_PINK]), legend=alt.Legend(title=None, orient="top")),
        tooltip=['EloBucket', 'Side', alt.Tooltip('PlayerCount', format=',')]
    ).properties(height=400)
    st.altair_chart(elo_dist_chart, width="stretch")

    st.divider()
    
    # --- ROW 2: Draw Rate Trend ---
    render_header("The Skill Effect: Draws by Rating", "How the likelihood of a draw increases as players get stronger")
    draw_trend_df = get_draw_rate_trend()
    
    draw_trend_chart = alt.Chart(draw_trend_df.to_pandas()).mark_area(
        color=NEON_PURPLE, opacity=0.25, line={'color': NEON_PURPLE, 'strokeWidth': 3}
    ).encode(
        x=alt.X('EloBucket:O', title="Rating Bracket", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('DrawRate:Q', title="Draw Percentage (%)", scale=alt.Scale(zero=False)),
        tooltip=['EloBucket', alt.Tooltip('DrawRate', format='.1f')]
    ).properties(height=400)
    
    # Adding stark white dots to make the individual data points stand out against the purple line
    draw_points = alt.Chart(draw_trend_df.to_pandas()).mark_circle(size=60, color=WHITE, opacity=1).encode(
        x='EloBucket:O', y='DrawRate:Q'
    )
    
    st.altair_chart(draw_trend_chart + draw_points, width="stretch")

# TAB 3: Specific Exploration
with tab3:
    render_header("Opening Deep Dive", "How does an opening perform across different skill levels?")
    
    selected_opening = st.selectbox("Select an opening", global_openings, label_visibility="collapsed")
    
    elo_win_rate_df = get_opening_win_rate_by_elo(selected_opening)
    
    if elo_win_rate_df.height > 0:
        base_op = alt.Chart(elo_win_rate_df.to_pandas())
        op_lines = base_op.mark_line(strokeWidth=2).encode(
            x=alt.X('EloBucket:O', title="Rating Bracket", axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('WinRate:Q', title="Win Rate (%)"),
            color=alt.Color('ResultLabel:N', scale=RESULT_SCALE, legend=alt.Legend(title=None, orient="top")),
            tooltip=['EloBucket', 'ResultLabel', alt.Tooltip('WinRate', format='.1f'), alt.Tooltip('GameVolume', format=',')]
        )
        op_dots = base_op.mark_circle(size=50, opacity=0.9).encode(
            x='EloBucket:O', y='WinRate:Q', color='ResultLabel:N'
        )
        st.altair_chart(op_lines + op_dots, width="stretch")
    else:
        st.info("Not enough data for this opening.")

# ── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("<p style='text-align: center; color: #555; font-size: 0.8rem; margin-top: 40px;'>LICHESS OPEN DATABASE · DUCKDB · POLARS · STREAMLIT</p>", unsafe_allow_html=True)