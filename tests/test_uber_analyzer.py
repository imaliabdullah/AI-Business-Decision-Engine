import pandas as pd
import pytest

from src.analysis.uber_analyzer import UberDataAnalyzer
from src.models.uber_schemas import UberAnalyticsResult


@pytest.fixture
def uber_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trip_id": range(1, 11),
            "driver_id": [101, 102, 103, 104, 105, 101, 106, 107, 108, 109],
            "rider_id": range(201, 211),
            "city": ["New York", "Boston", "New York", "Boston", "Chicago"] * 2,
            "pickup_lat": [40.7] * 10,
            "pickup_lng": [-74.0] * 10,
            "drop_lat": [40.71] * 10,
            "drop_lng": [-74.01] * 10,
            "distance_km": [5.0, 8.0, 3.0, 10.0, 6.0, 12.0, 4.0, 7.0, 2.0, 9.0],
            "fare_amount": [15.0, 20.0, 10.0, 25.0, 18.0, 30.0, 12.0, 22.0, 8.0, 24.0],
            "status": [
                "Completed", "Completed", "Cancelled", "Completed", "No-Show",
                "Completed", "Completed", "Cancelled", "Completed", "Completed",
            ],
            "payment_method": [
                "Card", "UPI", "Wallet", "Cash", "Card",
                "UPI", "Wallet", "Card", "Cash", "UPI",
            ],
            "pickup_time": pd.date_range("2023-01-01 08:00", periods=10, freq="10min"),
            "drop_time": pd.date_range("2023-01-01 08:20", periods=10, freq="10min"),
        }
    )


@pytest.fixture
def result(uber_df) -> UberAnalyticsResult:
    return UberDataAnalyzer.analyze(uber_df)


class TestUberKPIs:
    def test_total_trips(self, result):
        assert result.kpis.total_trips == 10

    def test_completed_trips(self, result):
        assert result.kpis.completed_trips == 7

    def test_cancelled_trips(self, result):
        assert result.kpis.cancelled_trips == 2

    def test_no_show_trips(self, result):
        assert result.kpis.no_show_trips == 1

    def test_completion_rate(self, result):
        assert result.kpis.completion_rate == 70.0

    def test_total_revenue_matches_completed_fares(self, uber_df, result):
        expected = uber_df[uber_df["status"] == "Completed"]["fare_amount"].sum()
        assert round(result.kpis.total_revenue, 2) == round(expected, 2)

    def test_unique_drivers(self, result):
        assert result.kpis.unique_drivers == 9

    def test_lost_revenue_is_positive(self, result):
        assert result.kpis.lost_revenue_estimate > 0


class TestCityMetrics:
    def test_returns_all_cities(self, result):
        cities = {m.city for m in result.city_metrics}
        assert cities == {"New York", "Boston", "Chicago"}

    def test_sorted_by_revenue_descending(self, result):
        revenues = [m.revenue for m in result.city_metrics]
        assert revenues == sorted(revenues, reverse=True)

    def test_cancellation_rate_within_bounds(self, result):
        for m in result.city_metrics:
            assert 0.0 <= m.cancellation_rate <= 100.0


class TestAnalyticsResult:
    def test_hourly_distribution_keys_are_ints(self, result):
        assert all(isinstance(k, int) for k in result.hourly_distribution)

    def test_payment_distribution_has_entries(self, result):
        assert len(result.payment_distribution) > 0

    def test_distance_segments_labels(self, result):
        expected_labels = {"<3km", "3-6km", "6-10km", "10-20km", ">20km"}
        assert set(result.distance_segments.keys()).issubset(expected_labels)

    def test_top_revenue_city_in_city_metrics(self, result):
        cities = {m.city for m in result.city_metrics}
        assert result.top_revenue_city in cities

    def test_top_cancellation_city_in_city_metrics(self, result):
        cities = {m.city for m in result.city_metrics}
        assert result.top_cancellation_city in cities

    def test_driver_single_trip_pct_within_bounds(self, result):
        assert 0.0 <= result.driver_single_trip_pct <= 100.0


class TestContextString:
    def test_context_contains_kpi_section(self, result):
        ctx = UberDataAnalyzer.build_context_string(result)
        assert "PLATFORM KPIs" in ctx

    def test_context_contains_all_sections(self, result):
        ctx = UberDataAnalyzer.build_context_string(result)
        for section in [
            "PLATFORM KPIs",
            "CITY PERFORMANCE",
            "HOURLY BOOKING",
            "CANCELLATION HOURS",
            "PAYMENT METHODS",
            "DISTANCE SEGMENTS",
            "DRIVER UTILIZATION",
        ]:
            assert section in ctx, f"Missing section: {section}"

    def test_context_contains_revenue_figure(self, result):
        ctx = UberDataAnalyzer.build_context_string(result)
        assert str(result.kpis.completed_trips) in ctx
