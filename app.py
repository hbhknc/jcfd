import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(
    page_title="Fire Rescue Incident Analytics",
    page_icon="🚒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Color Palette
FIRE_RED = "#FF4B4B"
DARK_BG = "#0E1117"
CARD_BG = "#1A1C24"
TEXT_COLOR = "#E0E0E0"
SUB_TEXT = "#999999"

# Custom CSS for Professional Dark Look with Depth
st.markdown(f"""
    <style>
    /* Main background */
    .stApp {{
        background-color: {DARK_BG};
        color: {TEXT_COLOR};
    }}

    /* Global font and headers */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .main-header {{
        font-size: 2.8rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
        text-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }}

    .sub-header {{
        font-size: 1.1rem;
        font-weight: 300;
        color: {SUB_TEXT};
        margin-bottom: 2rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }}

    /* Metric Card Styling */
    [data-testid="stMetricValue"] {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {FIRE_RED};
        text-shadow: 0px 0px 15px rgba(255, 75, 75, 0.3);
    }}

    [data-testid="stMetricLabel"] {{
        font-size: 0.85rem;
        font-weight: 600;
        color: {SUB_TEXT};
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }}

    /* Section Cards - Enhanced Depth with Glassmorphism-lite */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {CARD_BG} !important;
        border-radius: 1rem !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 1.5rem !important;
        transition: transform 0.3s ease;
    }}

    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border: 1px solid rgba(255, 75, 75, 0.2) !important;
    }}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: {DARK_BG};
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }}

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2.5rem;
        background-color: transparent;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 60px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0;
        border-bottom: 2px solid transparent;
        color: {SUB_TEXT} !important;
        font-weight: 400;
        transition: all 0.2s ease;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: transparent;
        border-bottom: 3px solid {FIRE_RED} !important;
        font-weight: 700 !important;
        color: white !important;
    }}

    /* Input fields refinement */
    .stTextInput>div>div>input {{
        background-color: #262730;
        color: white;
        border: 1px solid rgba(255,255,255,0.1);
    }}

    /* Scrollbar customization */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: {DARK_BG};
    }}
    ::-webkit-scrollbar-thumb {{
        background: #333;
        border-radius: 10px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: {FIRE_RED};
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Load Data
@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_fire_call_data_2020_2025_final.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month_name()
    df['Month_Num'] = df['Date'].dt.month
    df['Day_of_Week'] = df['Date'].dt.day_name()
    df['Day_Num'] = df['Date'].dt.dayofweek
    df['Quarter'] = "Q" + df['Date'].dt.quarter.astype(str)
    df = df.sort_values(by='Date')
    return df

df = load_data()

# 3. Filter Application Logic
def apply_filters(data, years, months, categories, days, search):
    f_df = data[
        (data['Year'].isin(years)) &
        (data['Month'].isin(months)) &
        (data['Standardized Call Category'].isin(categories)) &
        (data['Day_of_Week'].isin(days))
    ]
    if search:
        f_df = f_df[f_df['Notes'].str.contains(search, case=False, na=False)]
    return f_df

# 4. Sidebar Filters
with st.sidebar:
    st.image("JCFD Logo.png", use_container_width=True)
    st.markdown(f"<h2 style='color: white; text-align: center;'>Analytics Controls</h2>", unsafe_allow_html=True)
    st.divider()

    # Search by Keyword
    search_term = st.text_input("🔍 Search Notes (Keyword)", placeholder="e.g. 'unattended cooking'")

    with st.expander("📅 Time Filters", expanded=True):
        selected_years = st.multiselect(
            "Select Year(s)",
            options=sorted(df['Year'].unique(), reverse=True),
            default=df['Year'].unique()
        )

        months_order = ["January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"]
        selected_months = st.multiselect(
            "Select Month(s)",
            options=months_order,
            default=months_order
        )

        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        selected_days = st.multiselect(
            "Select Day(s) of Week",
            options=days_order,
            default=days_order
        )

    with st.expander("🚒 Incident Filters", expanded=True):
        selected_categories = st.multiselect(
            "Select Call Category",
            options=sorted(df['Standardized Call Category'].dropna().unique()),
            default=df['Standardized Call Category'].dropna().unique()
        )

    if st.button("🔄 Reset All Filters", width="stretch"):
        st.rerun()

    # Calculate filtered_df here so it can be used for sidebar stats
    filtered_df = apply_filters(df, selected_years, selected_months, selected_categories, selected_days, search_term)

    st.divider()
    st.markdown("### 📊 Dataset Overview")
    total_recs = len(df)
    filtered_recs = len(filtered_df)
    st.write(f"**Viewing:** {filtered_recs:,} / {total_recs:,} incidents")
    st.progress(filtered_recs / total_recs if total_recs > 0 else 0)

    st.markdown("""
    ---
    **System Status:** 🟢 Operational
    **Version:** 2.1.0
    """)

# 4. Main Dashboard Header
head_col1, head_col2 = st.columns([1, 5])
with head_col1:
    st.image("JCFD Logo.png", width=120)
with head_col2:
    st.markdown('<div class="main-header">Jordans Chapel Fire Department</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Incident Command Centre • Strategic Operational Analytics (2020 - 2025)</div>', unsafe_allow_html=True)

# 5. KPI Metrics
total_calls = len(filtered_df)
latest_date = filtered_df['Date'].max().strftime('%b %d, %Y') if not filtered_df.empty else "N/A"
top_category = filtered_df['Standardized Call Category'].mode()[0] if not filtered_df.empty else "N/A"
mutual_aid_calls = len(filtered_df[filtered_df['Standardized Call Category'].str.contains('Aid', na=False)])

yoy_text = None
if len(selected_years) == 1:
    current_year = selected_years[0]
    prev_year = current_year - 1
    if prev_year in df['Year'].unique():
        prev_year_df = apply_filters(df, [prev_year], selected_months, selected_categories, selected_days, search_term)
        prev_year_calls = len(prev_year_df)
        if prev_year_calls > 0:
            growth = ((total_calls - prev_year_calls) / prev_year_calls) * 100
            yoy_text = f"{growth:+.1f}% vs {prev_year}"

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("TOTAL INCIDENTS", f"{total_calls:,}", delta=yoy_text)
with kpi_cols[1]:
    st.metric("TOP CALL CATEGORY", top_category[:25] + "..." if len(top_category) > 25 else top_category)
with kpi_cols[2]:
    st.metric("MUTUAL AID CALLS", f"{mutual_aid_calls:,}")
with kpi_cols[3]:
    st.metric("LAST RECORDED INCIDENT", latest_date)

st.markdown("<br>", unsafe_allow_html=True)

# 6. Content Tabs
tab1, tab2, tab3 = st.tabs(["📊 EXECUTIVE SUMMARY", "📈 TREND ANALYSIS", "📋 INCIDENT EXPLORER"])

with tab1:
    # Summary Info Card
    with st.container(border=True):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            avg_monthly = total_calls / (len(selected_years) * 12) if selected_years else 0
            st.markdown(f"**Avg Incidents / Month**\n### {avg_monthly:.1f}")
        with sc2:
            st.markdown(f"**Active Reporting Period**\n### {len(selected_years)} Year(s)")
        with sc3:
            busy_day = filtered_df['Day_of_Week'].mode()[0] if not filtered_df.empty else "N/A"
            st.markdown(f"**Peak Activity Day**\n### {busy_day}")

    with st.container(border=True):
        st.subheader("📈 Monthly Incident Volume (Long-term Trend)")
        timeline_df = filtered_df.groupby([pd.Grouper(key='Date', freq='ME')]).size().reset_index(name='Count')
        fig_line = px.line(
            timeline_df, x='Date', y='Count',
            color_discrete_sequence=[FIRE_RED],
            markers=True,
            template="plotly_dark"
        )
        fig_line.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="", yaxis_title="Call Volume",
            margin=dict(l=0, r=0, t=10, b=0),
            height=350,
            hovermode="x unified"
        )
        st.plotly_chart(fig_line, width="stretch", use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        with st.container(border=True):
            st.subheader("🚒 Calls by Category")
            cat_df = filtered_df['Standardized Call Category'].value_counts().reset_index(name='Count')
            fig_bar = px.bar(
                cat_df, x='Count', y='Standardized Call Category',
                orientation='h', color='Count',
                color_continuous_scale=[[0, '#331111'], [1, FIRE_RED]],
                template="plotly_dark"
            )
            fig_bar.update_layout(
                yaxis={'categoryorder':'total ascending', 'title': ''},
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, width="stretch", use_container_width=True)

    with col_r:
        with st.container(border=True):
            st.subheader("🍕 Quarterly Distribution")
            q_df = filtered_df['Quarter'].value_counts().reset_index(name='Count').sort_values('Quarter')
            fig_pie = px.pie(
                q_df, values='Count', names='Quarter',
                hole=0.6, color_discrete_sequence=px.colors.sequential.Reds_r,
                template="plotly_dark"
            )
            fig_pie.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_pie, width="stretch", use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("📅 Volume by Day of Week")
            dow_df = filtered_df['Day_of_Week'].value_counts().reindex(days_order).reset_index(name='Count')
            fig_dow = px.bar(
                dow_df, x='Day_of_Week', y='Count',
                color='Count', color_continuous_scale=[[0, '#331111'], [1, FIRE_RED]],
                template="plotly_dark"
            )
            fig_dow.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title="", yaxis_title="",
                height=400, margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_dow, width="stretch", use_container_width=True)

    with col2:
        with st.container(border=True):
            st.subheader("🔥 Seasonal Patterns (Heatmap)")
            heatmap_data = filtered_df.groupby(['Month', 'Day_of_Week']).size().unstack(fill_value=0)
            heatmap_data = heatmap_data.reindex(index=months_order, columns=days_order, fill_value=0)
            fig_hm = px.imshow(
                heatmap_data,
                labels=dict(x="Day", y="Month", color="Calls"),
                color_continuous_scale="Reds",
                template="plotly_dark"
            )
            fig_hm.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400, margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig_hm, width="stretch", use_container_width=True)

    with st.container(border=True):
        st.subheader("📍 High-Frequency Locations (Top 10)")
        top_loc = filtered_df['Address'].value_counts().head(10).reset_index(name='Count')
        fig_loc = px.bar(
            top_loc, x='Count', y='Address',
            orientation='h', color='Count',
            color_continuous_scale=[[0, '#221133'], [1, '#BB86FC']],
            template="plotly_dark"
        )
        fig_loc.update_layout(
            yaxis={'categoryorder':'total ascending', 'title': ''},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_loc, width="stretch", use_container_width=True)

with tab3:
    with st.container(border=True):
        st.subheader("Incident Registry")
        st.info("💡 Use the sidebar search to filter incidents by keywords in the notes (e.g., 'cooking', 'accident', 'woods').")

        col_dl, col_sp = st.columns([1, 4])
        with col_dl:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Data (CSV)",
                data=csv,
                file_name='fire_rescue_export.csv',
                mime='text/csv',
                width="stretch"
            )

        st.dataframe(
            filtered_df[['Date', 'Incident #', 'Standardized Call Category', 'Address', 'Notes', 'Day_of_Week']],
            width="stretch",
            hide_index=True
        )

    if not filtered_df.empty:
        with st.container(border=True):
            st.subheader("🔍 Detailed Incident Lookup")
            selected_idx = st.selectbox(
                "Select an incident for full report details:",
                options=filtered_df.index,
                format_func=lambda x: f"{filtered_df.loc[x, 'Date'].strftime('%Y-%m-%d')} | {filtered_df.loc[x, 'Incident #']} | {filtered_df.loc[x, 'Standardized Call Category']}"
            )

            det = filtered_df.loc[selected_idx]
            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown(f"**INCIDENT NUMBER**\n{det['Incident #']}")
                st.markdown(f"**DATE / TIME**\n{det['Date'].strftime('%A, %B %d, %Y')}")
            with d2:
                st.markdown(f"**ADDRESS**\n{det['Address']}")
                st.markdown(f"**CATEGORY**\n{det['Standardized Call Category']}")
            with d3:
                st.markdown(f"**PROPERTY OWNER / DESC**\n{det['Property Owner / Desc.'] if pd.notna(det['Property Owner / Desc.']) else 'N/A'}")
                st.markdown(f"**CALL TYPE**\n{det['Call Type']}")

            st.markdown(f"**OFFICIAL NOTES:**")
            st.info(det['Notes'] if pd.notna(det['Notes']) and det['Notes'] != "" else "No notes recorded for this incident.")
