import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Nagpur Bus Analytics",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark modern styling
st.markdown("""
<style>
.stApp { background: #0b1120; color: #e5e7eb; }
[data-testid="stSidebar"] { background: #111827; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
h1, h2, h3 { color: #f8fafc; }
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #172033, #111827);
    border: 1px solid #263449;
    padding: 16px 18px;
    border-radius: 14px;
}
div[data-testid="stMetricLabel"] { color: #9ca3af; }
div[data-testid="stMetricValue"] { color: #f8fafc; }
div[data-testid="stAlert"] { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

DATA_FILE = Path(__file__).parent / "nagpur_city_bus_analytics_synthetic.csv"

@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
    elif DATA_FILE.exists():
        data = pd.read_csv(DATA_FILE)
    else:
        return None

    required = ["route_id", "route_name", "bus_stop", "hour",
                "passengers_onboard", "bus_capacity"]
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    if "date" in data.columns:
        data["date"] = pd.to_datetime(data["date"], errors="coerce")
    for c in ["hour", "passengers_onboard", "bus_capacity", "occupancy_percent",
              "estimated_wait_minutes"]:
        if c in data.columns:
            data[c] = pd.to_numeric(data[c], errors="coerce")

    data["occupancy_percent"] = (
        data["passengers_onboard"] / data["bus_capacity"].replace(0, pd.NA) * 100
    )
    data["occupancy_percent"] = data["occupancy_percent"].fillna(0).round(2)

    if "data_source" not in data.columns:
        data["data_source"] = "Unknown"
    return data

st.sidebar.title("🚌 Nagpur Bus Analytics")
st.sidebar.caption("Public Transport Demand & Occupancy")
st.sidebar.markdown("---")
uploaded = st.sidebar.file_uploader(
    "Optional: upload a CSV dataset",
    type=["csv"],
    help="The project CSV is loaded automatically when it is included in the app repository."
)

try:
    df = load_data(uploaded)
except Exception as e:
    st.error(f"Could not read the dataset: {e}")
    st.stop()

if df is None:
    st.error("Dataset not found. Add nagpur_city_bus_analytics_synthetic.csv beside app.py in your GitHub repository.")
    st.stop()

st.title("🚌 Nagpur Public Transport Analytics")
st.markdown("### Bus demand, route occupancy and peak-hour decision support")
st.caption("Prototype dashboard • Hadoop MapReduce + PySpark project")

st.info(
    "Demo data notice: this prototype uses synthetic demonstration data, not a live feed "
    "or official passenger counts from Nagpur buses. Insights are illustrative."
)

# Sidebar filters
filtered = df.copy()
if "date" in filtered.columns and filtered["date"].notna().any():
    valid_dates = filtered["date"].dropna()
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered = filtered[
            filtered["date"].dt.date.between(start_date, end_date)
        ]

route_options = sorted(filtered["route_name"].dropna().astype(str).unique())
selected_routes = st.sidebar.multiselect(
    "Routes",
    options=route_options,
    default=route_options
)
if selected_routes:
    filtered = filtered[filtered["route_name"].astype(str).isin(selected_routes)]

if "direction" in filtered.columns:
    direction_options = sorted(filtered["direction"].dropna().astype(str).unique())
    selected_directions = st.sidebar.multiselect(
        "Direction",
        options=direction_options,
        default=direction_options
    )
    if selected_directions:
        filtered = filtered[filtered["direction"].astype(str).isin(selected_directions)]

if "service_type" in filtered.columns:
    service_options = sorted(filtered["service_type"].dropna().astype(str).unique())
    selected_services = st.sidebar.multiselect(
        "Service type",
        options=service_options,
        default=service_options
    )
    if selected_services:
        filtered = filtered[filtered["service_type"].astype(str).isin(selected_services)]

if filtered.empty:
    st.warning("No records match these filters. Change the filters in the sidebar.")
    st.stop()

# KPI row
total_records = len(filtered)
route_count = filtered["route_id"].nunique()
stop_count = filtered["bus_stop"].nunique()
avg_occupancy = filtered["occupancy_percent"].mean()
capacity = filtered["bus_capacity"].replace(0, pd.NA)
overcrowded_pct = (filtered["occupancy_percent"] >= 85).mean() * 100

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Passenger observations", f"{total_records:,}")
c2.metric("Routes", f"{route_count:,}")
c3.metric("Stops", f"{stop_count:,}")
c4.metric("Average occupancy", f"{avg_occupancy:.1f}%")
c5.metric("Records ≥85% occupancy", f"{overcrowded_pct:.1f}%")

st.markdown("---")
left, right = st.columns([1.15, 1])

with left:
    st.subheader("Average occupancy by route")
    route_summary = (
        filtered.groupby(["route_id", "route_name"], as_index=False)
        .agg(avg_occupancy=("occupancy_percent", "mean"),
             observations=("passengers_onboard", "size"),
             avg_passengers=("passengers_onboard", "mean"))
        .sort_values("avg_occupancy", ascending=False)
    )
    route_summary["avg_occupancy"] = route_summary["avg_occupancy"].round(1)
    route_chart = px.bar(
        route_summary.head(12).sort_values("avg_occupancy"),
        x="avg_occupancy", y="route_name", orientation="h",
        color="avg_occupancy", color_continuous_scale="Teal",
        labels={"avg_occupancy": "Average occupancy (%)", "route_name": "Route"},
        hover_data={"route_id": True, "observations": True, "avg_passengers": ":.1f"}
    )
    route_chart.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=20, b=10), height=430
    )
    st.plotly_chart(route_chart, use_container_width=True)

with right:
    st.subheader("Occupancy by hour")
    hourly = (
        filtered.groupby("hour", as_index=False)
        .agg(avg_occupancy=("occupancy_percent", "mean"),
             avg_passengers=("passengers_onboard", "mean"))
        .sort_values("hour")
    )
    hourly["avg_occupancy"] = hourly["avg_occupancy"].round(1)
    hourly_chart = px.line(
        hourly, x="hour", y="avg_occupancy", markers=True,
        labels={"hour": "Hour of day (24-hour)", "avg_occupancy": "Average occupancy (%)"},
        hover_data={"avg_passengers": ":.1f"}
    )
    hourly_chart.update_traces(line_width=3)
    hourly_chart.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=20, b=10),
        height=430, xaxis=dict(dtick=1)
    )
    st.plotly_chart(hourly_chart, use_container_width=True)

st.markdown("---")
st.subheader("Peak-hour overview")
if not hourly.empty:
    peak_row = hourly.loc[hourly["avg_occupancy"].idxmax()]
    p1, p2, p3 = st.columns(3)
    p1.metric("Highest average occupancy hour", f"{int(peak_row['hour']):02d}:00")
    p2.metric("Occupancy at that hour", f"{peak_row['avg_occupancy']:.1f}%")
    p3.metric("Average passengers at that hour", f"{peak_row['avg_passengers']:.1f}")

st.subheader("Route-level decision support")
st.write("Routes are flagged for review when their average observed occupancy reaches 85% or more. This is a demonstration threshold, not an official transport policy.")
flagged = route_summary[route_summary["avg_occupancy"] >= 85]
if flagged.empty:
    st.success("No selected route crosses the demonstration threshold of 85% average occupancy.")
else:
    st.warning(f"{len(flagged)} selected route(s) cross the 85% average occupancy threshold.")
    for _, row in flagged.head(8).iterrows():
        st.write(
            f"**{row['route_name']}** — average occupancy {row['avg_occupancy']:.1f}%. "
            "Review passenger counts and consider whether peak-period capacity adjustments are warranted."
        )

st.markdown("---")
with st.expander("View filtered route summary"):
    st.dataframe(route_summary, use_container_width=True, hide_index=True)

with st.expander("View filtered dataset"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_nagpur_bus_analytics.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption(
    "Project: Public Transport Demand and Bus Occupancy Analytics using Hadoop and PySpark | "
    "Prototype built with Streamlit, Pandas and Plotly."
)
