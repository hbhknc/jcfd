
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

    call_types = sorted(df["Primary Call Type"].dropna().unique().tolist())
    selected_types = st.multiselect("Primary Call Type", call_types, default=call_types)

    address_search = st.text_input("Address contains", placeholder="e.g. US Highway")

filtered = df[
    df["Year"].isin(selected_years) &
    df["Primary Call Type"].isin(selected_types)
].copy()

if address_search.strip():
    filtered = filtered[filtered["Address"].str.contains(address_search.strip(), case=False, na=False)]

if filtered.empty:
    st.warning("No records match the current filters.")
    st.stop()

monthly = filtered.groupby("Month", as_index=False).size().rename(columns={"size": "Calls"})
call_mix = filtered.groupby("Primary Call Type", as_index=False).size().rename(columns={"size": "Calls"}).sort_values("Calls", ascending=False)
weekday = filtered.groupby("Weekday", as_index=False).size().rename(columns={"size": "Calls"})
month_name = filtered.groupby("Month Name", as_index=False).size().rename(columns={"size": "Calls"})
hotspots = filtered.groupby("Address", as_index=False).size().rename(columns={"size": "Calls"}).sort_values("Calls", ascending=False)

top_call_type = call_mix.iloc[0]["Primary Call Type"] if not call_mix.empty else "—"
busiest_address = hotspots.iloc[0]["Address"] if not hotspots.empty else "—"
avg_per_month = monthly["Calls"].mean() if not monthly.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Calls", format_int(len(filtered)))
c2.metric("Avg Calls / Month", f"{avg_per_month:.1f}")
c3.metric("Top Call Type", top_call_type)
c4.metric("Busiest Address", busiest_address)

tab1, tab2, tab3, tab4 = st.tabs(["Trends", "Call Mix", "Hotspots", "Data"])

with tab1:
    fig_monthly = px.line(
        monthly, x="Month", y="Calls", markers=True,
        title="Monthly Call Volume"
    )
    fig_monthly.update_layout(xaxis_title="", yaxis_title="Calls", height=420)
    st.plotly_chart(fig_monthly, use_container_width=True)

    c5, c6 = st.columns(2)
    with c5:
        fig_weekday = px.bar(weekday, x="Weekday", y="Calls", title="Calls by Weekday")
        fig_weekday.update_layout(xaxis_title="", yaxis_title="Calls", height=380)
        st.plotly_chart(fig_weekday, use_container_width=True)
    with c6:
        fig_monthname = px.bar(month_name, x="Month Name", y="Calls", title="Calls by Calendar Month")
        fig_monthname.update_layout(xaxis_title="", yaxis_title="Calls", height=380)
        st.plotly_chart(fig_monthname, use_container_width=True)

with tab2:
    fig_mix = px.bar(
        call_mix.head(15),
        x="Calls", y="Primary Call Type", orientation="h",
        title="Top Call Types"
    )
    fig_mix.update_layout(yaxis_title="", height=520)
    st.plotly_chart(fig_mix, use_container_width=True)

    fig_pie = px.pie(
        call_mix.head(10),
        names="Primary Call Type",
        values="Calls",
        title="Call Type Share (Top 10)"
    )
    fig_pie.update_layout(height=520)
    st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.subheader("Top Addresses")
    st.dataframe(
        hotspots.head(25),
        use_container_width=True,
        hide_index=True
    )

with tab4:
    show_cols = ["Date", "Address", "Primary Call Type", "Year"]
    st.dataframe(
        filtered[show_cols].sort_values("Date", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    csv_bytes = filtered[show_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered CSV",
        data=csv_bytes,
        file_name="jcfd_fire_calls_filtered.csv",
        mime="text/csv"
    )
