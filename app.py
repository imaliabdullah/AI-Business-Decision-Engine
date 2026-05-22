import pandas as pd
import plotly.express as px
import streamlit as st

from src.ai.insight_generator import InsightGenerator
from src.analysis.uber_analyzer import UberDataAnalyzer
from src.config.settings import UBER_ANALYSIS_ROWS, UBER_DATA_PATH
from src.data.loader import DataLoader

st.set_page_config(
    page_title="AI Business Decision Engine",
    layout="wide",
)

st.title("AI Business Decision Engine")
st.markdown("Uber Rides Intelligence — Executive analytics powered by AI.")
st.caption(
    f"Analysis based on the first **{UBER_ANALYSIS_ROWS:,} rows** "
    f"of `uber_trips_dataset_50k.csv`."
)


@st.cache_data
def load_uber_data() -> pd.DataFrame:
    return DataLoader.load_csv(str(UBER_DATA_PATH)).head(UBER_ANALYSIS_ROWS)


@st.cache_data
def compute_analytics(_df: pd.DataFrame):
    return UberDataAnalyzer.analyze(_df)


try:
    uber_df = load_uber_data()
    result = compute_analytics(uber_df)
    kpis = result.kpis

    with st.expander("Dataset Preview (first 5 rows)", expanded=False):
        st.dataframe(uber_df.head(), use_container_width=True)

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    st.subheader("Platform KPIs")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Trips", f"{kpis.total_trips:,}")
    k2.metric("Completed", f"{kpis.completed_trips:,}", f"{kpis.completion_rate}%")
    k3.metric(
        "Cancelled",
        f"{kpis.cancelled_trips:,}",
        f"-{kpis.cancellation_rate}%",
        delta_color="inverse",
    )
    k4.metric(
        "No-Shows",
        f"{kpis.no_show_trips:,}",
        f"-{kpis.no_show_rate}%",
        delta_color="inverse",
    )
    k5.metric("Total Revenue", f"${kpis.total_revenue:,.0f}")
    k6.metric(
        "Est. Lost Revenue",
        f"${kpis.lost_revenue_estimate:,.0f}",
        delta_color="inverse",
    )

    r2c1, r2c2, r2c3 = st.columns(3)
    r2c1.metric("Avg Fare", f"${kpis.avg_fare:.2f}")
    r2c2.metric("Avg Distance", f"{kpis.avg_distance_km:.2f} km")
    r2c3.metric("Avg Duration", f"{kpis.avg_duration_min:.1f} min")

    # ── City Performance ───────────────────────────────────────────────────────
    st.subheader("City Performance")

    city_df = pd.DataFrame(
        [
            {
                "City": m.city,
                "Revenue": m.revenue,
                "Avg Fare": m.avg_fare,
                "Cancellation Rate": m.cancellation_rate,
                "Fare per km": m.fare_per_km,
                "Completed Trips": m.completed_trips,
            }
            for m in result.city_metrics
        ]
    )

    ch1, ch2 = st.columns(2)
    with ch1:
        fig_rev = px.bar(
            city_df.sort_values("Revenue", ascending=True),
            x="Revenue",
            y="City",
            orientation="h",
            title="Revenue by City — Completed Trips ($)",
            color="Revenue",
            color_continuous_scale="Blues",
            text_auto=".2s",
            labels={"Revenue": "Revenue ($)"},
        )
        fig_rev.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig_rev, use_container_width=True)

    with ch2:
        fig_cancel = px.bar(
            city_df.sort_values("Cancellation Rate", ascending=True),
            x="Cancellation Rate",
            y="City",
            orientation="h",
            title="Cancellation Rate by City (%)",
            color="Cancellation Rate",
            color_continuous_scale="Reds",
            text_auto=".1f",
            labels={"Cancellation Rate": "Cancellation Rate (%)"},
        )
        fig_cancel.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig_cancel, use_container_width=True)

    # ── Operational Patterns ───────────────────────────────────────────────────
    st.subheader("Operational Patterns")

    hourly_df = pd.DataFrame(
        sorted(result.hourly_distribution.items()),
        columns=["Hour", "Trips"],
    )
    cancel_hourly_df = pd.DataFrame(
        sorted(result.cancellation_by_hour.items()),
        columns=["Hour", "Cancellation Rate (%)"],
    )

    ch3, ch4 = st.columns(2)
    with ch3:
        fig_hourly = px.bar(
            hourly_df,
            x="Hour",
            y="Trips",
            title="Hourly Booking Volume",
            color="Trips",
            color_continuous_scale="Teal",
        )
        fig_hourly.update_layout(
            coloraxis_showscale=False,
            xaxis=dict(tickmode="linear", dtick=1),
        )
        st.plotly_chart(fig_hourly, use_container_width=True)

    with ch4:
        fig_cancel_h = px.line(
            cancel_hourly_df,
            x="Hour",
            y="Cancellation Rate (%)",
            title="Cancellation Rate by Hour (%)",
            markers=True,
        )
        fig_cancel_h.update_traces(line_color="#EF553B", marker_color="#EF553B")
        fig_cancel_h.update_layout(xaxis=dict(tickmode="linear", dtick=1))
        fig_cancel_h.add_vline(
            x=result.peak_cancellation_hour,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Peak {result.peak_cancellation_hour_rate}%",
            annotation_position="top right",
        )
        st.plotly_chart(fig_cancel_h, use_container_width=True)

    # ── Market Insights ────────────────────────────────────────────────────────
    st.subheader("Market Insights")

    payment_df = pd.DataFrame(
        [
            {
                "Method": method,
                "Trips": count,
                "Avg Fare ($)": result.payment_avg_fare.get(method, 0),
            }
            for method, count in result.payment_distribution.items()
        ]
    ).sort_values("Trips", ascending=False)

    distance_df = pd.DataFrame(
        [
            {"Segment": seg, "Trips": count}
            for seg, count in result.distance_segments.items()
        ]
    )

    ch5, ch6 = st.columns(2)
    with ch5:
        fig_pay = px.pie(
            payment_df,
            names="Method",
            values="Trips",
            title="Payment Method Distribution",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_pay.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_pay, use_container_width=True)

    with ch6:
        fig_dist = px.bar(
            distance_df,
            x="Segment",
            y="Trips",
            title="Trip Distance Segmentation",
            color="Trips",
            color_continuous_scale="Purples",
            text_auto=True,
        )
        fig_dist.update_layout(coloraxis_showscale=False, xaxis_title="Distance Bucket")
        st.plotly_chart(fig_dist, use_container_width=True)

    # ── Revenue Efficiency ─────────────────────────────────────────────────────
    st.subheader("Revenue Efficiency")

    fig_fare_km = px.bar(
        city_df.sort_values("Fare per km", ascending=True),
        x="Fare per km",
        y="City",
        orientation="h",
        title="Average Fare per Kilometer by City ($)",
        color="Fare per km",
        color_continuous_scale="Greens",
        text_auto=".2f",
        labels={"Fare per km": "Fare per km ($)"},
    )
    fig_fare_km.update_layout(coloraxis_showscale=False, yaxis_title="")
    st.plotly_chart(fig_fare_km, use_container_width=True)

    # ── Driver Utilization ─────────────────────────────────────────────────────
    st.subheader("Driver Utilization")

    du1, du2, du3 = st.columns(3)
    du1.metric("Unique Drivers", f"{kpis.unique_drivers:,}")
    du2.metric("Avg Trips / Driver", f"{result.driver_utilization_mean:.2f}")
    du3.metric("Single-Trip Drivers", f"{result.driver_single_trip_pct:.1f}%")

    st.warning(
        f"**{result.driver_single_trip_pct:.1f}%** of active drivers completed only one trip — "
        f"indicating a transactional supply model with near-zero driver retention. "
        f"Only **{round(100 - result.driver_single_trip_pct, 1)}%** completed 2+ trips per session."
    )

    # ── AI-Powered Analysis ────────────────────────────────────────────────────
    st.divider()
    st.subheader("AI-Powered Uber Intelligence")
    st.info(
        "Generate executive-grade AI outputs grounded in the analyzed data. "
        "Each output uses only the computed metrics — no hallucination, no generic statements. "
        "Requires a valid **OPENAI_API_KEY** in your `.env` file."
    )

    btn1, btn2, btn3 = st.columns(3)

    with btn1:
        if st.button(
            "Generate Decision Brief",
            use_container_width=True,
            key="btn_brief",
            help="Situation · Findings · Risks · Opportunities · Actions · Recommendation",
        ):
            with st.spinner("Generating Decision Brief..."):
                gen = InsightGenerator()
                st.session_state["uber_brief"] = gen.generate_decision_brief(result)

    with btn2:
        if st.button(
            "Run Auto-Analyst",
            use_container_width=True,
            key="btn_analyst",
            help="8 auto-detected patterns: demand spikes, cancellation anomalies, driver gaps, and more",
        ):
            with st.spinner("Running Auto-Analyst..."):
                gen = InsightGenerator()
                st.session_state["uber_analyst"] = gen.generate_auto_analyst(result)

    with btn3:
        if st.button(
            "Generate Insight Summary",
            use_container_width=True,
            key="btn_summary",
            help="3 key takeaways · 1 critical risk · 1 recommended action",
        ):
            with st.spinner("Generating Insight Summary..."):
                gen = InsightGenerator()
                st.session_state["uber_summary"] = gen.generate_insight_summary(result)

    if "uber_brief" in st.session_state:
        st.subheader("Executive Decision Brief")
        st.markdown(st.session_state["uber_brief"])

    if "uber_analyst" in st.session_state:
        st.subheader("Auto-Analyst — 8 Detected Patterns")
        st.markdown(st.session_state["uber_analyst"])

    if "uber_summary" in st.session_state:
        st.subheader("Insight Summary")
        st.markdown(st.session_state["uber_summary"])

except Exception as err:
    st.error(f"Application error: {err}")
