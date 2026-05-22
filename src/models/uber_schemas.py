from dataclasses import dataclass


@dataclass
class UberKPIs:
    total_trips: int
    completed_trips: int
    cancelled_trips: int
    no_show_trips: int
    completion_rate: float
    cancellation_rate: float
    no_show_rate: float
    total_revenue: float
    avg_fare: float
    avg_distance_km: float
    avg_duration_min: float
    unique_drivers: int
    unique_riders: int
    lost_revenue_estimate: float

    def to_summary(self) -> str:
        return (
            f"Total Trips Analyzed: {self.total_trips}\n"
            f"Completed: {self.completed_trips} ({self.completion_rate}%)\n"
            f"Cancelled: {self.cancelled_trips} ({self.cancellation_rate}%)\n"
            f"No-Shows: {self.no_show_trips} ({self.no_show_rate}%)\n"
            f"Total Revenue (Completed Trips): ${self.total_revenue:,.2f}\n"
            f"Average Fare per Trip: ${self.avg_fare:.2f}\n"
            f"Average Distance: {self.avg_distance_km:.2f} km\n"
            f"Average Duration: {self.avg_duration_min:.1f} min\n"
            f"Unique Drivers Active: {self.unique_drivers}\n"
            f"Unique Riders: {self.unique_riders}\n"
            f"Estimated Lost Revenue (Cancellations + No-Shows): ${self.lost_revenue_estimate:,.2f}"
        )


@dataclass
class CityMetrics:
    city: str
    total_trips: int
    completed_trips: int
    revenue: float
    avg_fare: float
    cancellation_rate: float
    fare_per_km: float


@dataclass
class UberAnalyticsResult:
    kpis: UberKPIs
    city_metrics: list[CityMetrics]
    hourly_distribution: dict[int, int]
    cancellation_by_hour: dict[int, float]
    payment_distribution: dict[str, int]
    payment_avg_fare: dict[str, float]
    distance_segments: dict[str, int]
    driver_utilization_mean: float
    driver_single_trip_pct: float
    top_cancellation_city: str
    top_revenue_city: str
    top_fare_per_km_city: str
    peak_cancellation_hour: int
    peak_cancellation_hour_rate: float
