# AI Business Decision Engine — Uber Rides Intelligence

An AI-powered analytics platform that analyzes the first 1,000 rows of an Uber trips dataset
and generates executive-grade insights for a ride-booking platform.

## What It Does

### 1. Decision Brief Generator
Produces a structured executive brief covering situation summary, key findings, operational
risks, business opportunities, five recommended actions, and a board-level recommendation —
grounded entirely in the computed data.

### 2. Auto-Analyst
Automatically detects and explains 8 operational patterns:
- Demand spikes and hourly volume distribution
- High-revenue locations and fare-per-km efficiency
- Peak hours and demand shape
- Cancellation anomalies by city and hour
- Payment behavior and customer segmentation
- Trip distance trends and fleet deployment implications
- Driver utilization and retention gaps
- Most efficient booking windows

### 3. Insight Summary
Generates three data-backed executive takeaways, one critical operational risk,
and one highest-priority recommended action — formatted for CEO-level review.

## Project Structure

```
project/
├── app.py                          # Streamlit entry point (single-page)
├── requirements.txt
├── .env                            # API keys (not committed)
├── README.md
│
├── data/
│   └── uber_trips_dataset_50k.csv  # Source dataset (first 1,000 rows analyzed)
│
├── src/
│   ├── config/
│   │   └── settings.py             # Centralised configuration (paths, model, thresholds)
│   ├── data/
│   │   └── loader.py               # CSV loading with path validation
│   ├── analysis/
│   │   └── uber_analyzer.py        # All KPI, city, hourly, driver, and distance analytics
│   ├── ai/
│   │   ├── llm_client.py           # OpenAI wrapper (model, temperature, error handling)
│   │   ├── prompts.py              # Three structured prompt templates
│   │   └── insight_generator.py    # Prompt orchestration — ties analytics to LLM
│   ├── utils/
│   │   ├── logger.py               # Structured logging across all modules
│   │   └── helpers.py              # Formatting utilities
│   └── models/
│       └── uber_schemas.py         # Typed dataclasses: UberKPIs, CityMetrics, UberAnalyticsResult
│
└── tests/
    └── test_uber_analyzer.py       # 20 unit tests covering KPIs, city metrics, and context generation
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
# Edit .env and set your OpenAI API key
OPENAI_API_KEY=your_key_here
```

### 3. Run the app

```bash
streamlit run app.py
```

### 4. Run tests

```bash
pytest tests/ -v
```

## Dashboard Sections

| Section | Content |
|---|---|
| Platform KPIs | 9 metric cards — trips, revenue, cancellations, no-shows, lost revenue, avg fare/distance/duration |
| City Performance | Revenue by city · Cancellation rate by city |
| Operational Patterns | Hourly booking volume · Cancellation rate by hour with peak marker |
| Market Insights | Payment method distribution · Trip distance segmentation |
| Revenue Efficiency | Fare per km by city |
| Driver Utilization | Unique drivers · Avg trips per driver · Single-trip driver % |
| AI Analysis | Decision Brief · Auto-Analyst · Insight Summary (on-demand, cached in session) |

## Architecture Decisions

| Decision | Rationale |
|---|---|
| `UberDataAnalyzer` with static methods | Stateless analytics — no side effects, fully testable |
| `UberAnalyticsResult` dataclass | Single typed object passed through the entire pipeline |
| `build_context_string()` on analyzer | Serialises computed metrics into LLM-ready text — keeps prompts data-grounded |
| Three separate prompt templates | Each AI task has a distinct role, structure, and output contract |
| `st.session_state` for AI outputs | AI results persist across Streamlit reruns without re-calling the API |
| `@st.cache_data` on data load and analytics | Prevents re-reading and re-computing on every UI interaction |
| On-demand AI buttons | No accidental API calls on page load; user controls when to spend tokens |
