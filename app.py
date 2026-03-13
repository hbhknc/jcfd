
import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="JCFD Fire Calls Dashboard",
    page_icon="🚒",
    layout="wide",
)

DATA_FILE = Path(__file__).parent / "JCFD Fire Calls - Dashboard v1.xlsx"

@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    else:
        if DATA_FILE.exists():
            df = pd.read_excel(DATA_FILE)
        else:
            return pd.DataFrame(columns=["Date", "Address", "Primary Call Type"])

    # Normalize expected columns
    rename_map = {c: c.strip() for c in df.columns}
    df = df.rename(columns=rename_map)

    expected = ["Date", "Address", "Primary Call Type"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    df = df[expected].copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Address"] = df["Address"].fillna("Unknown").astype(str).str.strip()
    df["Primary Call Type"] = df["Primary Call Type"].fillna("Unknown").astype(str).str.strip()

    df = df.dropna(subset=["Date"]).sort_values("Date")
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["Month Label"] = df["Date"].dt.strftime("%Y-%m")
    df["Month Name"] = pd.Categorical(
        df["Date"].dt.strftime("%b"),
        categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        ordered=True,
    )
    df["Weekday"] = pd.Categorical(
        df["Date"].dt.strftime("%a"),
        categories=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        ordered=True,
    )
    df["Hour"] = df["Date"].dt.hour
    return df

def format_int(value):
    return f"{int(value):,}" if pd.notna(value) else "—"

st.title("🚒 JCFD Fire Calls Dashboard")
st.caption("Interactive analysis of fire call activity from the uploaded log.")

with st.sidebar:
    st.header("Controls")
    uploaded = st.file_uploader("Upload a fire call log", type=["xlsx", "xls", "csv"])
    st.caption("If no file is uploaded, the bundled workbook is used.")

try:
    df = load_data(uploaded)
except Exception as e:
    st.error(f"Could not load the file: {e}")
    st.stop()

if df.empty:
    st.warning("No usable rows found.")
    st.stop()

with st.sidebar:
    years = sorted(df["Year"].dropna().unique().tolist())
    selected_years = st.multiselect("Year", years, default=years)

    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    selected_date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    call_types = sorted(df["Primary Call Type"].dropna().unique().tolist())
    selected_types = st.multiselect("Primary Call Type", call_types, default=call_types)

    address_search = st.text_input("Address contains", placeholder="e.g. US Highway")
    top_n = st.slider("Top N categories", min_value=5, max_value=30, value=15)

if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    selected_start, selected_end = selected_date_range
else:
    selected_start, selected_end = min_date, max_date

selected_start_ts = pd.Timestamp(selected_start)
selected_end_ts = pd.Timestamp(selected_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

filtered = df[
    df["Year"].isin(selected_years) &
    df["Primary Call Type"].isin(selected_types) &
    df["Date"].between(selected_start_ts, selected_end_ts)
].copy()

if address_search.strip():
    filtered = filtered[filtered["Address"].str.contains(address_search.strip(), case=False, na=False)]

if filtered.empty:
    st.warning("No records match the current filters.")
    st.stop()

monthly = filtered.groupby("Month", as_index=False).size().rename(columns={"size": "Calls"})
monthly = monthly.sort_values("Month")
monthly["Rolling 3-Month Avg"] = monthly["Calls"].rolling(window=3, min_periods=1).mean()

call_mix = filtered.groupby("Primary Call Type", as_index=False).size().rename(columns={"size": "Calls"}).sort_values("Calls", ascending=False)
weekday = filtered.groupby("Weekday", as_index=False, observed=False).size().rename(columns={"size": "Calls"})
month_name = filtered.groupby("Month Name", as_index=False, observed=False).size().rename(columns={"size": "Calls"})
hotspots = filtered.groupby("Address", as_index=False).size().rename(columns={"size": "Calls"}).sort_values("Calls", ascending=False)
yearly = filtered.groupby("Year", as_index=False).size().rename(columns={"size": "Calls"})

days_selected = (selected_end_ts.normalize() - selected_start_ts.normalize()).days + 1
prev_end_ts = selected_start_ts - pd.Timedelta(seconds=1)
prev_start_ts = prev_end_ts - pd.Timedelta(days=max(days_selected - 1, 0))

previous_period = df[
    df["Primary Call Type"].isin(selected_types) &
    df["Date"].between(prev_start_ts, prev_end_ts)
].copy()
if address_search.strip():
    previous_period = previous_period[
        previous_period["Address"].str.contains(address_search.strip(), case=False, na=False)
    ]

prev_total_calls = len(previous_period)
call_delta_pct = ((len(filtered) - prev_total_calls) / prev_total_calls * 100) if prev_total_calls else None

top_call_type = call_mix.iloc[0]["Primary Call Type"] if not call_mix.empty else "—"
busiest_address = hotspots.iloc[0]["Address"] if not hotspots.empty else "—"
avg_per_month = monthly["Calls"].mean() if not monthly.empty else 0

c1, c2, c3, c4 = st.columns(4, vertical_alignment="top")
c1.metric(
    "Total Calls",
    format_int(len(filtered)),
    delta=(f"{call_delta_pct:+.1f}% vs prior period" if call_delta_pct is not None else "No prior-period data"),
)
c2.metric("Avg Calls / Month", f"{avg_per_month:.1f}")
c3.metric("Top Call Type", top_call_type)
c4.metric("Busiest Address", busiest_address)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Trends", "Call Mix", "Hotspots", "Data", "Data Quality"])

with tab1:
    fig_monthly = px.line(
        monthly,
        x="Month",
        y=["Calls", "Rolling 3-Month Avg"],
        markers=True,
        title="Monthly Call Volume",
        template="plotly_dark",
        color_discrete_sequence=["#D62728", "#FFD166"],
    )
    fig_monthly.update_layout(xaxis_title="", yaxis_title="Calls", height=420, legend_title_text="Series")
    st.plotly_chart(fig_monthly, width="stretch")

    c5, c6 = st.columns(2, vertical_alignment="top")
    with c5:
        fig_weekday = px.bar(
            weekday,
            x="Weekday",
            y="Calls",
            title="Calls by Weekday",
            color="Calls",
            color_continuous_scale="Reds",
            template="plotly_dark",
        )
        fig_weekday.update_layout(xaxis_title="", yaxis_title="Calls", height=380, showlegend=False)
        st.plotly_chart(fig_weekday, width="stretch")
    with c6:
        fig_monthname = px.bar(
            month_name,
            x="Month Name",
            y="Calls",
            title="Calls by Calendar Month",
            color="Calls",
            color_continuous_scale="Reds",
            template="plotly_dark",
        )
        fig_monthname.update_layout(xaxis_title="", yaxis_title="Calls", height=380, showlegend=False)
        st.plotly_chart(fig_monthname, width="stretch")

    fig_yearly = px.bar(
        yearly,
        x="Year",
        y="Calls",
        title="Calls by Year",
        color="Calls",
        color_continuous_scale="Reds",
        template="plotly_dark",
    )
    fig_yearly.update_layout(height=420, xaxis_title="", yaxis_title="Calls")
    st.plotly_chart(fig_yearly, width="stretch")

with tab2:
    fig_mix = px.bar(
        call_mix.head(top_n),
        x="Calls",
        y="Primary Call Type",
        orientation="h",
        title="Top Call Types",
        color="Calls",
        color_continuous_scale="Reds",
        template="plotly_dark",
    )
    fig_mix.update_layout(yaxis_title="", height=520, showlegend=False)
    st.plotly_chart(fig_mix, width="stretch")

    fig_pie = px.pie(
        call_mix.head(min(top_n, 10)),
        names="Primary Call Type",
        values="Calls",
        title="Call Type Share (Top 10)",
        template="plotly_dark"
    )
    fig_pie.update_layout(height=520)
    st.plotly_chart(fig_pie, width="stretch")

with tab3:
    st.subheader("Top Addresses")
    st.dataframe(
        hotspots.head(top_n),
        width="stretch",
        hide_index=True
    )

with tab4:
    show_cols = ["Date", "Address", "Primary Call Type", "Year"]
    st.dataframe(
        filtered[show_cols].sort_values("Date", ascending=False),
        width="stretch",
        hide_index=True
    )

    csv_bytes = filtered[show_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered CSV",
        data=csv_bytes,
        file_name="jcfd_fire_calls_filtered.csv",
        mime="text/csv",
        width="stretch"
    )

with tab5:
    st.subheader("Data quality checks")
    duplicate_rows = filtered.duplicated(subset=["Date", "Address", "Primary Call Type"]).sum()
    unknown_address = (filtered["Address"].str.lower() == "unknown").sum()
    unknown_call_type = (filtered["Primary Call Type"].str.lower() == "unknown").sum()

    q1, q2, q3 = st.columns(3)
    q1.metric("Potential duplicate rows", format_int(duplicate_rows))
    q2.metric("Unknown addresses", format_int(unknown_address))
    q3.metric("Unknown call types", format_int(unknown_call_type))

    st.caption("Duplicates are counted by matching Date + Address + Primary Call Type.")
