import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Fire Rescue Incident Dashboard", page_icon="🚒", layout="wide")

# 2. Load Data (Cache it so it loads fast and simulates real-time efficiency)
@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_fire_call_data_2020_2025_final.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month_name()
    # Sort for chronological charting
    df = df.sort_values(by='Date')
    return df

df = load_data()

# 3. Sidebar Filters (PowerBI style "Slicers")
st.sidebar.header("Filter Data")
selected_years = st.sidebar.multiselect(
    "Select Year(s):",
    options=df['Year'].unique(),
    default=df['Year'].unique()
)

selected_categories = st.sidebar.multiselect(
    "Select Call Category:",
    options=df['Standardized Call Category'].dropna().unique(),
    default=df['Standardized Call Category'].dropna().unique()
)

# Apply filters
filtered_df = df[
    (df['Year'].isin(selected_years)) & 
    (df['Standardized Call Category'].isin(selected_categories))
]

# 4. Main Dashboard Header & KPI Cards
st.title("🚒 Fire Rescue Call Dashboard")
st.markdown("Interactive, real-time dashboard tracking incident trends and call categories.")

# KPI Metrics
col1, col2, col3, col4 = st.columns(4)
total_calls = len(filtered_df)
latest_date = filtered_df['Date'].max().strftime('%Y-%m-%d') if not filtered_df.empty else "N/A"
top_category = filtered_df['Standardized Call Category'].mode()[0] if not filtered_df.empty else "N/A"
mutual_aid_calls = len(filtered_df[filtered_df['Standardized Call Category'].str.contains('Aid', na=False)])

col1.metric("Total Incidents (Selected)", total_calls)
col2.metric("Most Frequent Call Type", top_category)
col3.metric("Mutual Aid / Support Given", mutual_aid_calls)
col4.metric("Last Incident Recorded", latest_date)

st.divider()

# 5. Visualizations
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Calls Over Time")
    # Group by Year-Month for a smooth timeline
    timeline_df = filtered_df.set_index('Date').resample('M').size().reset_index(name='Incident Count')
    fig_line = px.line(
        timeline_df, 
        x='Date', 
        y='Incident Count',
        markers=True,
        line_shape='spline',
        color_discrete_sequence=['#d62728']
    )
    fig_line.update_layout(xaxis_title="Month", yaxis_title="Total Calls", margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.subheader("Breakdown by Category")
    cat_df = filtered_df['Standardized Call Category'].value_counts().reset_index()
    cat_df.columns = ['Category', 'Count']
    fig_bar = px.bar(
        cat_df, 
        x='Count', 
        y='Category', 
        orientation='h',
        color='Count',
        color_continuous_scale='Reds'
    )
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# 6. Detailed Data Table (PowerBI style Matrix)
st.subheader("Raw Data View")
st.dataframe(
    filtered_df[['Date', 'Incident #', 'Standardized Call Category', 'Address', 'Notes']],
    use_container_width=True,
    hide_index=True
)