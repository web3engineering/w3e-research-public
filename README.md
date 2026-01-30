# W3E Research - Polymarket Analytics

Research dashboards and analytics for Polymarket data, powered by [PredictionLabs.ch](https://predictionlabs.ch).

## Available Dashboards

### 📊 Upcoming Events Dashboard
Location: `src/apps/upcoming_events/`

Displays Polymarket events that will finish soon, sorted by time remaining.

**Features:**
- Real-time data from ClickHouse
- Active events only
- Interactive search and filtering
- Event images, questions, expiration times, and 24h volume
- Configurable display limits (10-200 events)

**Run:**
```bash
uv run streamlit run src/apps/upcoming_events/dashboard.py
```

See [src/apps/upcoming_events/README.md](src/apps/upcoming_events/README.md) for details.

### 📈 Pre-Resolution Strategy Analysis
Location: `src/apps/pre_resolution_analysis/`

Analyzes a trading strategy that leverages high-confidence price signals shortly before market resolution. Identifies markets where the price was above a threshold Y minutes before resolution and calculates the win rate and expected value (EV).

**Features:**
- Configurable parameters (days back, price threshold, minutes before resolution)
- Win/loss distribution pie chart
- Expected value (EV) calculation
- Detailed trade history with downloadable CSV
- Real-time analysis of historical data

**Run:**
```bash
uv run streamlit run src/apps/pre_resolution_analysis/dashboard.py
```

See [src/apps/pre_resolution_analysis/README.md](src/apps/pre_resolution_analysis/README.md) for details.

## Setup

### Prerequisites
- Python 3.12+
- uv package manager

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Configure environment variables in `.env`:
   ```
   POLY_CLICKHOUSE_URL=host:port
   POLY_CLICKHOUSE_USER=username
   POLY_CLICKHOUSE_PASSWORD=password
   ```

## Development

### Project Structure
```
src/
├── core/              # Core utilities and database accessors
│   ├── clickhouse.py  # PolymarketAccessor, HyperLiquidAccessor
│   └── environment.py # Environment variable loading
└── apps/              # Dashboard applications
    └── upcoming_events/
        ├── dashboard.py           # Streamlit app
        ├── get_upcoming_events.py # Helper functions
        ├── test_get_upcoming_events.py # Tests
        └── README.md
```

### Testing
Each dashboard includes test scripts:
```bash
cd src/apps/upcoming_events
PYTHONPATH=/root/w3e-research-public:$PYTHONPATH uv run python test_get_upcoming_events.py
```

## Data Attribution

All data is provided by [PredictionLabs.ch](https://predictionlabs.ch)
