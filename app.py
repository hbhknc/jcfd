import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="Fire Rescue Incident Dashboard", page_icon="🚒", layout="wide")

# Custom CSS for better styling
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #d62728;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Load Data (Cache it so it loads fast and simulates real-time efficiency)
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
    # Sort for chronological charting
    df = df.sort_values(by='Date')
    return df

df = load_data()

# 3. Sidebar Filters
st.sidebar.image("https://img.icons8.com/emoji/96/000000/fire-engine.png", width=100)
st.sidebar.header("🔍 Global Filters")

# Search by Keyword
search_term = st.sidebar.text_input("Search Notes (Keyword):", "")

selected_years = st.sidebar.multiselect(
    "Select Year(s):",
    options=sorted(df['Year'].unique(), reverse=True),
    default=df['Year'].unique()
)

months_order = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]
selected_months = st.sidebar.multiselect(
    "Select Month(s):",
    options=months_order,
    default=months_order
)

selected_categories = st.sidebar.multiselect(
    "Select Call Category:",
    options=sorted(df['Standardized Call Category'].dropna().unique()),
    default=df['Standardized Call Category'].dropna().unique()
)

days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
selected_days = st.sidebar.multiselect(
    "Select Day(s) of Week:",
    options=days_order,
    default=days_order
)

# Function to apply filters (used for current and previous year comparison)
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

# Apply filters to get current selection
filtered_df = apply_filters(df, selected_years, selected_months, selected_categories, selected_days, search_term)

# 4. Main Dashboard Header
st.markdown('<p class="main-header">🚒 Fire Rescue Incident Dashboard</p>', unsafe_allow_html=True)
st.markdown("---")

# 5. KPI Metrics (Calculated for current selection)
total_calls = len(filtered_df)
latest_date = filtered_df['Date'].max().strftime('%Y-%m-%d') if not filtered_df.empty else "N/A"
top_category = filtered_df['Standardized Call Category'].mode()[0] if not filtered_df.empty else "N/A"
mutual_aid_calls = len(filtered_df[filtered_df['Standardized Call Category'].str.contains('Aid', na=False)])

# Calculate YoY Growth if single year is selected
yoy_text = ""
if len(selected_years) == 1:
    current_year = selected_years[0]
    prev_year = current_year - 1
    if prev_year in df['Year'].unique():
        # Apply same filters but for the previous year
        prev_year_df = apply_filters(df, [prev_year], selected_months, selected_categories, selected_days, search_term)
        prev_year_calls = len(prev_year_df)
        if prev_year_calls > 0:
            growth = ((total_calls - prev_year_calls) / prev_year_calls) * 100
            yoy_text = f"{growth:+.1f}% vs last year"
        else:
            yoy_text = "N/A (No data for prev year)"

# Display KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Incidents", f"{total_calls:,}", delta=yoy_text if yoy_text else None)
kpi2.metric("Top Call Category", top_category)
kpi3.metric("Mutual Aid Calls", f"{mutual_aid_calls:,}")
kpi4.metric("Last Incident", latest_date)

st.markdown("---")

# 6. Tabs for better organization
tab1, tab2, tab3 = st.tabs(["📊 Executive Summary", "📈 Incident Analysis", "📋 Data Explorer"])

with tab1:
    st.subheader("High-Level Trends")

    # Calls Over Time (Grouped by Month) - Using 'ME' for Month End frequency as per deprecation warning
    timeline_df = filtered_df.groupby([pd.Grouper(key='Date', freq='ME')]).size().reset_index(name='Incident Count')
    fig_line = px.line(
        timeline_df,
        x='Date',
        y='Incident Count',
        markers=True,
        line_shape='spline',
        title="Monthly Incident Volume",
        color_discrete_sequence=['#d62728']
    )
    fig_line.update_layout(
        xaxis_title="Timeline",
        yaxis_title="Total Calls",
        height=400,
        hovermode="x unified",
        template="plotly_white"
    )
    st.plotly_chart(fig_line, width='stretch')

    col_left, col_right = st.columns(2)
    with col_left:
        # Category Breakdown
        cat_df = filtered_df['Standardized Call Category'].value_counts().reset_index()
        cat_df.columns = ['Category', 'Count']
        fig_bar = px.bar(
            cat_df,
            x='Count',
            y='Category',
            orientation='h',
            title="Incidents by Category",
            color='Count',
            color_continuous_scale='Reds'
        )
        fig_bar.update_layout(
            yaxis={'categoryorder':'total ascending'},
            height=450,
            template="plotly_white"
        )
        st.plotly_chart(fig_bar, width='stretch')

    with col_right:
        # Calls by Quarter
        q_df = filtered_df['Quarter'].value_counts().reset_index()
        q_df.columns = ['Quarter', 'Count']
        q_df = q_df.sort_values('Quarter')
        fig_pie = px.pie(
            q_df,
            values='Count',
            names='Quarter',
            title="Distribution by Quarter",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Reds_r
        )
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, width='stretch')

with tab2:
    st.subheader("Detailed Incident Patterns")

    col1, col2 = st.columns(2)

    with col1:
        # Day of Week Analysis
        dow_df = filtered_df['Day_of_Week'].value_counts().reindex(days_order).reset_index()
        dow_df.columns = ['Day', 'Count']
        fig_dow = px.bar(
            dow_df,
            x='Day',
            y='Count',
            title="Calls by Day of Week",
            color='Count',
            color_continuous_scale='Oranges'
        )
        fig_dow.update_layout(template="plotly_white")
        st.plotly_chart(fig_dow, width='stretch')

    with col2:
        # Heatmap: Day of Week vs Month
        heatmap_data = filtered_df.groupby(['Month', 'Day_of_Week']).size().unstack(fill_value=0)
        # Reorder with fill_value=0 to handle missing combinations
        heatmap_data = heatmap_data.reindex(index=months_order, columns=days_order, fill_value=0)

        fig_heatmap = px.imshow(
            heatmap_data,
            labels=dict(x="Day of Week", y="Month", color="Incidents"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            aspect="auto",
            title="Incident Heatmap (Month vs Day of Week)",
            color_continuous_scale='YlOrRd'
        )
        st.plotly_chart(fig_heatmap, width='stretch')

    # Top Locations (Addresses)
    st.subheader("Top Incident Locations")
    top_loc_df = filtered_df['Address'].value_counts().head(10).reset_index()
    top_loc_df.columns = ['Address', 'Count']
    fig_loc = px.bar(
        top_loc_df,
        x='Count',
        y='Address',
        orientation='h',
        title="Top 10 Responded Addresses",
        color='Count',
        color_continuous_scale='Purples'
    )
    fig_loc.update_layout(yaxis={'categoryorder':'total ascending'}, template="plotly_white")
    st.plotly_chart(fig_loc, width='stretch')

with tab3:
    st.subheader("Incident Data Explorer")

    col1, col2 = st.columns([1, 4])
    with col1:
        # Download Button
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name='filtered_fire_incidents.csv',
            mime='text/csv',
            width='stretch'
        )

    # Searchable Dataframe
    st.dataframe(
        filtered_df[['Date', 'Incident #', 'Standardized Call Category', 'Address', 'Notes', 'Day_of_Week']],
        width='stretch',
        hide_index=True
    )
