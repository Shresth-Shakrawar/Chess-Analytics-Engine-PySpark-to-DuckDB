import streamlit as st
import altair as alt
from pipeline.queries import get_kpis, get_opening_efficacy, get_draw_rate_trend, get_popular_openings, get_opening_win_rate_by_elo

# --- ALTAIR DARK MODE SERIF THEME ---
@alt.theme.register("dark_serif", enable=True)
def dark_serif_theme():
    font = "Merriweather"
    text_color = "#F1F5F9" # Bright off-white for dark mode legibility
    grid_color = "#334155" # Subtle dark grey for grid lines
    
    return alt.theme.ThemeConfig(
        {
            "config": {
                "background": "transparent", # Lets Streamlit's dark background show through
                "title": {"font": font, "fontSize": 18, "fontWeight": 700, "color": text_color},
                "axis": {
                    "labelFont": font,
                    "titleFont": font,
                    "titleFontWeight": 700,
                    "labelFontSize": 12,
                    "titleFontSize": 14,
                    "labelColor": text_color,
                    "titleColor": text_color,
                    "gridColor": grid_color,
                    "domainColor": grid_color,
                    "tickColor": grid_color
                },
                "legend": {
                    "labelFont": font,
                    "titleFont": font,
                    "titleFontWeight": 700,
                    "labelFontSize": 12,
                    "titleFontSize": 13,
                    "labelColor": text_color,
                    "titleColor": text_color,
                    "padding": 10
                },
                "view": {
                    "stroke": "transparent" 
                }
            }
        }
    )

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Chess Analytics Pro", page_icon="♟️", layout="wide")

# --- CUSTOM CSS FOR DARK MODE & SERIF FONT ---
# --- CUSTOM CSS FOR DARK MODE, SERIF FONT & KPI CARDS ---
st.markdown("""
    <style>
    /* Import Merriweather from Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;0,900;1,400&display=swap');
    
    /* Apply it globally */
    html, body, [class*="css"]  {
        font-family: 'Merriweather', serif !important;
    }
    
    /* --- THE KPI CARD STYLING --- */
    [data-testid="metric-container"] {
        background-color: #1E293B; /* Slight contrast against the black background */
        border: 1px solid #334155; /* Subtle slate border */
        padding: 15px 20px;        /* Breathing room inside the card */
        border-radius: 8px;        /* Rounded corners */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); /* Soft drop shadow for depth */
    }

    /* Make the metric numbers bright and elegant */
    [data-testid="stMetricValue"] {
        font-weight: 900;
        color: #F8FAFC !important; 
    }
    
    /* Subdue the metric labels slightly */
    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-style: italic;
    }
    </style>
""", unsafe_allow_html=True)

st.title("♟️ Professional Chess Analytics")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Data Filters")
elo_range = st.sidebar.slider("Filter by Player Elo:", min_value=800, max_value=2800, value=(1400, 2000), step=50)
min_elo, max_elo = elo_range[0], elo_range[1]

# --- FETCH DATA ---
kpis = get_kpis(min_elo, max_elo)
efficacy_df = get_opening_efficacy(min_elo, max_elo)
draw_trend_df = get_draw_rate_trend()

# --- TOPLEVEL SCORECARDS ---
st.markdown("### Top-Level KPIs")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Games Analyzed", f"{kpis['total_games']:,}")
col2.metric("First-Move Advantage", f"{kpis['white_win_rate']:.1f}%")
col3.metric("Average Elo", f"{kpis['avg_elo']:,}")
col4.metric("Most Played Opening", kpis['top_opening'])

st.divider()

# --- HIGH-CONTRAST DARK MODE PALETTE ---
color_scale = alt.Scale(
    domain=['White Win', 'Draw', 'Black Win'],
    range=['#E2E8F0', '#64748B', '#F43F5E'] # Silver, Slate Grey, Neon Rose
)

# --- GRAPH 1: OPENING EFFICACY (100% Stacked Bar) ---
st.subheader("Opening Efficacy (100% Stacked)")
st.write("Visualizing the decisiveness of the top 10 openings. Are they bloody battles or drawish?")

efficacy_chart = alt.Chart(efficacy_df.to_pandas()).mark_bar().encode(
    x=alt.X('sum(count):Q', stack="normalize", axis=alt.Axis(format='%', title="Percentage of Outcomes")),
    y=alt.Y('BaseOpening:N', sort='-x', title="Opening"),
    color=alt.Color('ResultLabel:N', scale=color_scale, legend=alt.Legend(title="Match Result", orient="top")),
    tooltip=['BaseOpening', 'ResultLabel', 'count']
).properties(height=400)

st.altair_chart(efficacy_chart, width="stretch")

st.divider()

# --- GRAPH 2: DRAW RATE VS ELO (Line Graph) ---
st.subheader("Global Draw Rate vs. Player Rating")
st.write("Does chess become more drawish at the Master level? (Shows global data, ignores sidebar filters).")

draw_line = alt.Chart(draw_trend_df.to_pandas()).mark_line(color='#38BDF8', strokeWidth=4).encode(
    x=alt.X('EloBucket:O', title="Average Match Elo"),
    y=alt.Y('DrawRate:Q', title="Draw Rate (%)"),
    tooltip=['EloBucket', 'DrawRate', 'GameVolume']
).properties(height=350)

draw_points = draw_line.mark_circle(size=80, color='#BAE6FD')
st.altair_chart(draw_line + draw_points, width="stretch")

st.divider()

# --- GRAPH 3: OPENING WIN RATE BY ELO (Multi-line Chart) ---
st.subheader("Deep Dive: Opening Performance by Skill Level")
st.write("How does the meta shift as players get stronger? Select an opening to see its win rates across Elo brackets.")

available_openings = get_popular_openings()
selected_opening = st.selectbox("Choose an Opening to Analyze:", available_openings, index=0)

elo_win_rate_df = get_opening_win_rate_by_elo(selected_opening)

if elo_win_rate_df.height > 0:
    opening_elo_line = alt.Chart(elo_win_rate_df.to_pandas()).mark_line(strokeWidth=3).encode(
        x=alt.X('EloBucket:O', title="Average Match Elo", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('WinRate:Q', title="Win Rate (%)"),
        color=alt.Color('ResultLabel:N', scale=color_scale, legend=alt.Legend(title="Result", orient="top")),
        tooltip=['EloBucket', 'ResultLabel', alt.Tooltip('WinRate:Q', format='.1f'), 'GameVolume']
    ).properties(height=400)

    opening_elo_points = opening_elo_line.mark_circle(size=70)
    st.altair_chart(opening_elo_line + opening_elo_points, width="stretch")
else:
    st.warning("Not enough data to map this opening across Elo brackets.")