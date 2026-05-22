import pandas as pd

from src.models.uber_schemas import CityMetrics, UberAnalyticsResult, UberKPIs
from src.utils.logger import get_logger

logger = get_logger(__name__)

_DISTANCE_BINS = [0, 3, 6, 10, 20, 1000]
_DISTANCE_LABELS = ["<3km", "3-6km", "6-10km", "10-20km", ">20km"]


class UberDataAnalyzer:
    """Computes all ride-level KPIs and operational patterns from Uber trip data."""

    @staticmethod
    def analyze(df: pd.DataFrame) -> UberAnalyticsResult:
        df = df.copy()
        df["pickup_time"] = pd.to_datetime(df["pickup_time"])
        df["drop_time"] = pd.to_datetime(df["drop_time"])
        df["duration_min"] = (
            (df["drop_time"] - df["pickup_time"]).dt.total_seconds() / 60
        )
        df["hour"] = df["pickup_time"].dt.hour
        # Guard against division by zero on distance
        df["fare_per_km"] = df.apply(
            lambda r: r["fare_amount"] / r["distance_km"] if r["distance_km"] > 0 else 0,
            axis=1,
        )

        completed = df[df["status"] == "Completed"]
        cancelled = df[df["status"] == "Cancelled"]
        no_show = df[df["status"] == "No-Show"]

        total = len(df)
        total_revenue = round(completed["fare_amount"].sum(), 2)
        avg_fare = round(completed["fare_amount"].mean(), 2) if len(completed) else 0
        lost_revenue = round((len(cancelled) + len(no_show)) * avg_fare, 2)

        kpis = UberKPIs(
            total_trips=total,
            completed_trips=len(completed),
            cancelled_trips=len(cancelled),
            no_show_trips=len(no_show),
            completion_rate=round(len(completed) / total * 100, 2),
            cancellation_rate=round(len(cancelled) / total * 100, 2),
            no_show_rate=round(len(no_show) / total * 100, 2),
            total_revenue=total_revenue,
            avg_fare=avg_fare,
            avg_distance_km=round(completed["distance_km"].mean(), 2) if len(completed) else 0,
            avg_duration_min=round(completed["duration_min"].mean(), 1) if len(completed) else 0,
            unique_drivers=int(df["driver_id"].nunique()),
            unique_riders=int(df["rider_id"].nunique()),
            lost_revenue_estimate=lost_revenue,
        )

        # Per-city metrics
        city_metrics: list[CityMetrics] = []
        for city, grp in df.groupby("city"):
            comp = grp[grp["status"] == "Completed"]
            cancel_rate = (grp["status"] == "Cancelled").sum() / len(grp) * 100
            city_metrics.append(
                CityMetrics(
                    city=str(city),
                    total_trips=len(grp),
                    completed_trips=len(comp),
                    revenue=round(comp["fare_amount"].sum(), 2),
                    avg_fare=round(comp["fare_amount"].mean(), 2) if len(comp) else 0,
                    cancellation_rate=round(cancel_rate, 2),
                    fare_per_km=round(comp["fare_per_km"].mean(), 2) if len(comp) else 0,
                )
            )
        city_metrics.sort(key=lambda x: x.revenue, reverse=True)

        # Hourly booking volume
        hourly_dist: dict[int, int] = {
            int(h): int(c) for h, c in df.groupby("hour").size().items()
        }

        # Cancellation rate by hour
        cancel_by_hour: dict[int, float] = {}
        for hour, grp in df.groupby("hour"):
            rate = (grp["status"] == "Cancelled").sum() / len(grp) * 100
            cancel_by_hour[int(hour)] = round(rate, 2)

        # Payment method breakdown
        payment_dist: dict[str, int] = {
            str(k): int(v) for k, v in df["payment_method"].value_counts().items()
        }
        payment_avg: dict[str, float] = {
            str(k): round(float(v), 2)
            for k, v in df.groupby("payment_method")["fare_amount"].mean().items()
        }

        # Distance segmentation
        df["dist_bucket"] = pd.cut(
            df["distance_km"],
            bins=_DISTANCE_BINS,
            labels=_DISTANCE_LABELS,
        )
        dist_segments: dict[str, int] = {
            str(k): int(v)
            for k, v in df["dist_bucket"].value_counts().sort_index().items()
        }

        # Driver utilization
        driver_trips = completed.groupby("driver_id").size()
        driver_util_mean = round(float(driver_trips.mean()), 2) if len(driver_trips) else 0
        driver_single_pct = (
            round((driver_trips == 1).sum() / len(driver_trips) * 100, 1)
            if len(driver_trips) else 0
        )

        top_cancel_city = max(city_metrics, key=lambda x: x.cancellation_rate).city
        top_revenue_city = city_metrics[0].city if city_metrics else ""
        top_fare_km_city = max(city_metrics, key=lambda x: x.fare_per_km).city if city_metrics else ""

        peak_cancel_hour = max(cancel_by_hour, key=cancel_by_hour.get) if cancel_by_hour else 0
        peak_cancel_rate = cancel_by_hour.get(peak_cancel_hour, 0.0)

        logger.info("Uber analysis complete: %d trips processed", total)

        return UberAnalyticsResult(
            kpis=kpis,
            city_metrics=city_metrics,
            hourly_distribution=hourly_dist,
            cancellation_by_hour=cancel_by_hour,
            payment_distribution=payment_dist,
            payment_avg_fare=payment_avg,
            distance_segments=dist_segments,
            driver_utilization_mean=driver_util_mean,
            driver_single_trip_pct=driver_single_pct,
            top_cancellation_city=top_cancel_city,
            top_revenue_city=top_revenue_city,
            top_fare_per_km_city=top_fare_km_city,
            peak_cancellation_hour=peak_cancel_hour,
            peak_cancellation_hour_rate=peak_cancel_rate,
        )

    @staticmethod
    def build_context_string(result: UberAnalyticsResult) -> str:
        """Serialize analytics result into an LLM-ready context block."""
        city_rows = "\n".join(
            f"  {m.city}: revenue=${m.revenue:,.2f}, completed_trips={m.completed_trips}, "
            f"avg_fare=${m.avg_fare:.2f}, cancellation_rate={m.cancellation_rate}%, "
            f"fare_per_km=${m.fare_per_km:.2f}"
            for m in result.city_metrics
        )

        top_cancel_hours = sorted(
            result.cancellation_by_hour.items(), key=lambda x: x[1], reverse=True
        )[:8]
        cancel_hourly_str = ", ".join(
            f"Hour {h}:00 = {r}%" for h, r in top_cancel_hours
        )

        payment_str = "\n".join(
            f"  {method}: {count} trips, avg_fare=${result.payment_avg_fare.get(method, 0):.2f}"
            for method, count in result.payment_distribution.items()
        )

        distance_str = "\n".join(
            f"  {segment}: {count} trips"
            for segment, count in result.distance_segments.items()
        )

        hourly_str = ", ".join(
            f"Hour {h}:00={c}" for h, c in sorted(result.hourly_distribution.items())
        )

        return f"""
=== PLATFORM KPIs (First 1,000 Trips) ===
{result.kpis.to_summary()}

=== CITY PERFORMANCE (sorted by revenue) ===
{city_rows}

=== HOURLY BOOKING DISTRIBUTION ===
{hourly_str}

=== TOP CANCELLATION HOURS ===
{cancel_hourly_str}

=== PAYMENT METHODS ===
{payment_str}

=== TRIP DISTANCE SEGMENTS ===
{distance_str}

=== DRIVER UTILIZATION ===
Average trips per driver per session: {result.driver_utilization_mean}
Drivers completing only 1 trip: {result.driver_single_trip_pct}%
Top cancellation city: {result.top_cancellation_city}
Top revenue city: {result.top_revenue_city}
Highest fare-per-km city: {result.top_fare_per_km_city}
Peak cancellation hour: {result.peak_cancellation_hour}:00 ({result.peak_cancellation_hour_rate}% cancellation rate)
"""
