import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(
    page_title="Fire Rescue Incident Analytics",
    page_icon="🚒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Color Palette
FIRE_RED = "#D62728"
DARK_GREY = "#2C3E50"
LIGHT_GREY = "#ECF0F1"
ACCENT_BLUE = "#3498DB"

# Custom CSS for Professional Look
st.markdown(f"""
    <style>
    /* Main background */
    .stApp {{
        background-color: #F8F9FA;
    }}

    /* Global font and headers */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .main-header {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {DARK_GREY};
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
    }}

    .sub-header {{
        font-size: 1.2rem;
        color: #7F8C8D;
        margin-bottom: 2rem;
    }}

    /* Metric Card Styling */
    [data-testid="stMetricValue"] {{
        font-size: 2.2rem;
        font-weight: 700;
        color: {FIRE_RED};
    }}

    [data-testid="stMetricLabel"] {{
        font-size: 1rem;
        font-weight: 600;
        color: {DARK_GREY};
    }}

    /* Section Cards - Styling Streamlit containers with border */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: white;
        border-radius: 0.8rem !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        border: 1px solid #E9ECEF !important;
        padding: 1rem !important;
    }}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: white;
        border-right: 1px solid #E9ECEF;
    }}

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2rem;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: transparent;
        border-bottom: 3px solid {FIRE_RED} !important;
        font-weight: 700;
        color: {FIRE_RED} !important;
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
    st.image("https://img.icons8.com/color/96/000000/fire-station.png", width=80)
    st.markdown(f"<h2 style='color: {DARK_GREY};'>Analytics Controls</h2>", unsafe_allow_html=True)
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
st.markdown('<div class="main-header">🚒 Fire Rescue Incident Command Centre</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Strategic analytics and operational tracking for fire rescue operations (2020 - 2025)</div>', unsafe_allow_html=True)

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
    with st.container(border=True):
        st.subheader("Monthly Incident Volume (Long-term Trend)")
        timeline_df = filtered_df.groupby([pd.Grouper(key='Date', freq='ME')]).size().reset_index(name='Count')
        fig_line = px.line(
            timeline_df, x='Date', y='Count',
            color_discrete_sequence=[FIRE_RED],
            markers=True
        )
        fig_line.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="", yaxis_title="Call Volume",
            margin=dict(l=0, r=0, t=10, b=0),
            height=350,
            hovermode="x unified"
        )
        st.plotly_chart(fig_line, width="stretch")

    col_l, col_r = st.columns(2)
    with col_l:
        with st.container(border=True):
            st.subheader("Calls by Category")
            cat_df = filtered_df['Standardized Call Category'].value_counts().reset_index(name='Count')
            fig_bar = px.bar(
                cat_df, x='Count', y='Standardized Call Category',
                orientation='h', color='Count',
                color_continuous_scale=[[0, '#FADBD8'], [1, FIRE_RED]]
            )
            fig_bar.update_layout(
                yaxis={'categoryorder':'total ascending', 'title': ''},
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, width="stretch")

    with col_r:
        with st.container(border=True):
            st.subheader("Quarterly Distribution")
            q_df = filtered_df['Quarter'].value_counts().reset_index(name='Count').sort_values('Quarter')
            fig_pie = px.pie(
                q_df, values='Count', names='Quarter',
                hole=0.6, color_discrete_sequence=px.colors.sequential.Reds_r
            )
            fig_pie.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_pie, width="stretch")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Volume by Day of Week")
            dow_df = filtered_df['Day_of_Week'].value_counts().reindex(days_order).reset_index(name='Count')
            fig_dow = px.bar(
                dow_df, x='Day_of_Week', y='Count',
                color='Count', color_continuous_scale=[[0, '#FADBD8'], [1, FIRE_RED]]
            )
            fig_dow.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="", yaxis_title="",
                height=400, margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_dow, width="stretch")

    with col2:
        with st.container(border=True):
            st.subheader("Seasonal Patterns (Heatmap)")
            heatmap_data = filtered_df.groupby(['Month', 'Day_of_Week']).size().unstack(fill_value=0)
            heatmap_data = heatmap_data.reindex(index=months_order, columns=days_order, fill_value=0)
            fig_hm = px.imshow(
                heatmap_data,
                labels=dict(x="Day", y="Month", color="Calls"),
                color_continuous_scale="Reds"
            )
            fig_hm.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_hm, width="stretch")

    with st.container(border=True):
        st.subheader("High-Frequency Locations (Top 10)")
        top_loc = filtered_df['Address'].value_counts().head(10).reset_index(name='Count')
        fig_loc = px.bar(
            top_loc, x='Count', y='Address',
            orientation='h', color='Count',
            color_continuous_scale=[[0, '#E8DAEF'], [1, '#8E44AD']]
        )
        fig_loc.update_layout(
            yaxis={'categoryorder':'total ascending', 'title': ''},
            plot_bgcolor='rgba(0,0,0,0)',
            height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_loc, width="stretch")

with tab3:
    with st.container(border=True):
        st.subheader("Incident Registry")

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
