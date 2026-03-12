import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from datetime import timedelta

# 1. Page Configuration - MUST BE FIRST
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
    /* 1. Global Background Reset - Aggressive */
    html, body, .stApp, .stAppViewContainer, .stMain, .stHeader,
    [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stHeader"], [data-testid="stApp"], [data-testid="stToolbar"] {{
        background-color: {DARK_BG} !important;
        color: {TEXT_COLOR} !important;
    }}

    /* 2. Remove any header/toolbar borders and backgrounds */
    header[data-testid="stHeader"], [data-testid="stHeader"] {{
        background-color: transparent !important;
        background: transparent !important;
        border-bottom: none !important;
    }}

    [data-testid="stToolbar"] {{
        right: 2rem;
        background-color: transparent !important;
    }}

    /* 3. Global Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

    * {{
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

    /* 4. Metric Card Styling */
    [data-testid="stMetricValue"] {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {FIRE_RED} !important;
        text-shadow: 0px 0px 15px rgba(255, 75, 75, 0.3);
    }}

    [data-testid="stMetricLabel"] {{
        font-size: 0.85rem;
        font-weight: 600;
        color: {SUB_TEXT};
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }}

    /* 5. Section Cards - Enhanced Depth */
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

    /* 6. Sidebar styling */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    [data-testid="stSidebarNav"] {{
        background-color: {DARK_BG} !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }}

    /* 7. Tabs styling */
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

    /* 8. Input fields refinement */
    .stTextInput>div>div>input {{
        background-color: #262730 !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }}

    /* 9. Scrollbar customization */
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
    st.image("JCFD Logo.png", width="stretch")
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
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 EXECUTIVE SUMMARY",
    "📈 TREND ANALYSIS",
    "📋 INCIDENT EXPLORER",
    "🔮 PREDICTIVE INSIGHTS"
])

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
        st.subheader("⏱️ Incident Frequency & Intervals")
        # Calculate days between incidents for the filtered dataset
        if len(filtered_df) > 1:
            temp_df = filtered_df.sort_values('Date')
            temp_df['Days_Since_Last'] = temp_df['Date'].diff().dt.days
            avg_interval = temp_df['Days_Since_Last'].mean()
            max_gap = temp_df['Days_Since_Last'].max()

            i1, i2, i3 = st.columns(3)
            with i1:
                st.metric("Avg Days Between Calls", f"{avg_interval:.1f} Days")
            with i2:
                st.metric("Longest Gap", f"{max_gap:.0f} Days")
            with i3:
                # Frequency per 100 days
                freq_100 = (len(filtered_df) / ((temp_df['Date'].max() - temp_df['Date'].min()).days + 1)) * 100
                st.metric("Calls per 100 Days", f"{freq_100:.1f}")
        else:
            st.info("Insufficient data for interval analysis.")

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
        st.plotly_chart(fig_line, width="stretch")

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
            st.plotly_chart(fig_bar, width="stretch")

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
            st.plotly_chart(fig_pie, width="stretch")

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
            st.plotly_chart(fig_dow, width="stretch")

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
            st.plotly_chart(fig_hm, width="stretch")

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
        st.plotly_chart(fig_loc, width="stretch")

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

with tab4:
    st.markdown("### 🔮 Operational Intelligence & Forecasting")

    f1, f2 = st.columns([2, 1])

    with f1:
        with st.container(border=True):
            st.subheader("📈 6-Month Volume Forecast")
            # Prepare data for forecasting
            forecast_df = df.groupby(pd.Grouper(key='Date', freq='ME')).size().reset_index(name='Count')
            forecast_df['Ordinal'] = np.arange(len(forecast_df))

            if len(forecast_df) > 12:
                # Linear Regression
                X = forecast_df[['Ordinal']]
                y = forecast_df['Count']
                model = LinearRegression()
                model.fit(X, y)

                # Predict next 6 months
                last_ordinal = forecast_df['Ordinal'].max()
                future_ordinals = np.arange(last_ordinal + 1, last_ordinal + 7).reshape(-1, 1)
                future_preds = model.predict(future_ordinals)

                # Create future dates
                last_date = forecast_df['Date'].max()
                future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, 7)]

                prediction_df = pd.DataFrame({
                    'Date': future_dates,
                    'Count': future_preds,
                    'Status': 'Forecast'
                })
                forecast_df['Status'] = 'Historical'

                combined_forecast = pd.concat([forecast_df[['Date', 'Count', 'Status']], prediction_df])

                fig_forecast = px.line(
                    combined_forecast, x='Date', y='Count', color='Status',
                    color_discrete_map={'Historical': FIRE_RED, 'Forecast': '#BB86FC'},
                    line_dash='Status',
                    template="plotly_dark",
                    labels={'Count': 'Monthly Incidents'}
                )
                fig_forecast.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_forecast, width="stretch")
                st.caption("Forecast based on linear trend of historical monthly volumes (2020-2025).")
            else:
                st.warning("Insufficient historical data to generate a reliable forecast.")

    with f2:
        with st.container(border=True):
            st.subheader("🤝 Mutual Aid Balance")
            # Analyze aid balance
            aid_given = len(df[df['Auto / Mutual Aid Given Reference'].notna()])
            aid_received = len(df[df['Auto / Mutual Aid Received'].notna() & (df['Auto / Mutual Aid Received'] != "")])

            aid_df = pd.DataFrame({
                'Type': ['Aid Given', 'Aid Received'],
                'Count': [aid_given, aid_received]
            })

            fig_aid = px.bar(
                aid_df, x='Type', y='Count',
                color='Type', color_discrete_map={'Aid Given': FIRE_RED, 'Aid Received': '#4B9BFF'},
                template="plotly_dark"
            )
            fig_aid.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                xaxis_title="",
                yaxis_title="Total Incidents"
            )
            st.plotly_chart(fig_aid, width="stretch")
            st.caption("Lifetime Mutual Aid relationship balance.")

        with st.container(border=True):
            st.subheader("🚒 Unit Utilization")
            # Heuristic: Check notes for engine/brush truck keywords
            brush_calls = len(df[df['Notes'].str.contains('Brush|Woods|Grass', case=False, na=False)])
            engine_calls = len(df[df['Notes'].str.contains('Engine|Structure|Fire', case=False, na=False)])
            rescue_calls = len(df[df['Notes'].str.contains('Rescue|Extrication|MVC', case=False, na=False)])

            unit_df = pd.DataFrame({
                'Unit': ['Engine / Fire', 'Brush / Woods', 'Rescue / MVC'],
                'Incidents': [engine_calls, brush_calls, rescue_calls]
            })

            fig_unit = px.pie(
                unit_df, values='Incidents', names='Unit',
                color_discrete_sequence=px.colors.sequential.YlOrRd_r,
                hole=0.4, template="plotly_dark"
            )
            fig_unit.update_layout(
                margin=dict(l=0,r=0,t=10,b=0), height=250, showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_unit, width="stretch")
            st.caption("Estimated unit deployment based on incident narrative keywords.")

    st.markdown("---")

    c1, c2 = st.columns([1, 2])

    with c1:
        with st.container(border=True):
            st.subheader("☁️ Narrative Intelligence")
            # Generate Word Cloud from Filtered Notes
            all_notes = " ".join(filtered_df['Notes'].fillna("").astype(str))
            if len(all_notes.strip()) > 10:
                wordcloud = WordCloud(
                    width=800, height=800,
                    background_color=DARK_BG,
                    colormap='Reds',
                    min_font_size=10
                ).generate(all_notes)

                fig_wc, ax = plt.subplots(figsize=(8, 8))
                ax.imshow(wordcloud)
                ax.axis("off")
                fig_wc.patch.set_facecolor(DARK_BG)
                st.pyplot(fig_wc)
                st.caption("Most frequent terms found in incident narratives.")
            else:
                st.info("Not enough narrative data to generate word cloud.")

        with st.container(border=True):
            st.subheader("🔍 Keyword Seasonality")
            kw_to_track = st.text_input("Track Keyword Seasonality", value="cooking", key="kw_track")
            if kw_to_track:
                kw_df = df[df['Notes'].str.contains(kw_to_track, case=False, na=False)]
                if not kw_df.empty:
                    kw_seasonal = kw_df['Month'].value_counts().reindex(months_order, fill_value=0).reset_index()
                    kw_seasonal.columns = ['Month', 'Volume']
                    fig_kw = px.line(kw_seasonal, x='Month', y='Volume', markers=True,
                                     color_discrete_sequence=['#FFD700'], template="plotly_dark")
                    fig_kw.update_layout(height=250, margin=dict(l=0,r=0,t=10,b=0), xaxis_title="", yaxis_title="")
                    st.plotly_chart(fig_kw, width="stretch")
                    st.caption(f"Historical seasonal trend for incidents mentioning '{kw_to_track}'.")
                else:
                    st.warning(f"No incidents found containing '{kw_to_track}'.")

    with c2:
        with st.container(border=True):
            st.subheader("⚡ Operational Stress Analysis")
            # Calculate incidents per day to find "peak stress" days
            stress_df = filtered_df.groupby('Date').size().reset_index(name='Daily_Volume')
            stress_bins = stress_df['Daily_Volume'].value_counts().sort_index().reset_index()
            stress_bins.columns = ['Incidents_in_Day', 'Frequency']

            fig_stress = px.bar(
                stress_bins, x='Incidents_in_Day', y='Frequency',
                labels={'Incidents_in_Day': 'Incidents per 24h Window', 'Frequency': 'Days with this Volume'},
                template="plotly_dark",
                color='Frequency',
                color_continuous_scale="Reds"
            )
            fig_stress.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_stress, width="stretch")
            st.caption("Distribution of daily incident load (detecting multi-call days).")
