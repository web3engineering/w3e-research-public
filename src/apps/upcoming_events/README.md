# Upcoming Events Dashboard

Dashboard displaying Polymarket events that will finish soon, sorted by time remaining.

## Features

- **Real-time Data**: Fetches current Polymarket events from the database
- **Sorted by Time**: Events are sorted by end date (ascending), showing the most urgent first
- **Active Events Only**: Only displays currently active events
- **Deduplication**: Handles duplicate metadata rows by selecting the most recent insert
- **Interactive Table**:
  - Event images
  - Market questions
  - Time remaining until expiration
  - End dates in UTC
  - 24-hour trading volume
- **Search**: Filter events by keyword
- **Configurable Limit**: Adjust the number of events displayed (10-200)

## Running the Dashboard

### Method 1: From Repository Root (Recommended)

```bash
cd /root/w3e-research-public
uv run streamlit run src/apps/upcoming_events/dashboard.py
```

### Method 2: From Any Directory

```bash
uv run streamlit run /root/w3e-research-public/src/apps/upcoming_events/dashboard.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`

## Technical Details

### Data Source

- **Database**: ClickHouse (PredictionLabs.ch)
- **Table**: `polymarket.raw_market_meta`
- **Filters**:
  - `active = TRUE`
  - `end_date > now()`
  - Latest `inserted_at` per market ID

### Query Logic

The dashboard uses a window function to deduplicate metadata rows:
1. Partition by market `id` (not by `clob_token_id` to avoid showing both Yes/No outcomes)
2. Order by `inserted_at DESC` to get the latest metadata
3. Filter for `rn = 1` to get only the most recent row per market
4. Apply `DISTINCT` to ensure uniqueness

### Helper Functions

- `get_upcoming_events(limit)`: Fetches events from database
- `format_time_to_expire(seconds)`: Formats time as "Xd Yh Zm"
- `format_volume(amount)`: Formats volume as "$X.XM" or "$XXK"

## Testing

Test the helper functions:

```bash
cd src/apps/upcoming_events
PYTHONPATH=/root/w3e-research-public:$PYTHONPATH uv run python test_get_upcoming_events.py
```

This runs unit tests for:
- Time formatting
- Volume formatting
- Database queries

## Environment Variables

Required in `.env` file at repository root:
- `POLY_CLICKHOUSE_URL`: ClickHouse host:port
- `POLY_CLICKHOUSE_USER`: Database username
- `POLY_CLICKHOUSE_PASSWORD`: Database password

## Data Attribution

Data provided by [PredictionLabs.ch](https://predictionlabs.ch)
