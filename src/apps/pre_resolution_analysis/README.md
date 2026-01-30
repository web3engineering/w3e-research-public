# Pre-Resolution Trading Strategy Analysis

## Overview

This dashboard analyzes a trading strategy on Polymarket that leverages high-confidence price signals shortly before market resolution.

## Strategy Description

The strategy works as follows:

1. Look at historical resolved markets from the last N days
2. For each market, check the price Y minutes before resolution
3. If the price was within range [X_min, X_max], consider it a "qualifying trade"
4. Check if the `outcome_price` (actual resolution value) is >= X_min (indicating a win)
5. Calculate win rate and expected value (EV) using actual average entry prices

**Note**: Win/loss determination uses the `outcome_price` column from market metadata, which represents the actual settlement value, not the last trade price.

## Metrics

- **Win Rate**: Percentage of qualifying trades that resulted in wins
- **Average Entry Price**: Mean price of all qualifying trades
- **Expected Value (EV)**: Average profit/loss per $1 wagered
  - When you win: gain (1.0 - avg_entry_price) per $1 wagered
  - When you lose: lose avg_entry_price per $1 wagered
  - EV = (win_rate × gain) - (loss_rate × loss)

## Parameters

- **N (Historical Days)**: Number of days to look back (1-7 days, default: 7)
- **X_min (Min Price)**: Minimum price threshold (default: 0.98)
- **X_max (Max Price)**: Maximum price threshold (default: 1.00)
- **Y (Minutes Before)**: How many minutes before resolution to check the price (default: 2)

## Files

- `analyze_strategy.py`: Core analysis logic
- `test_analyze_strategy.py`: Test script to verify functionality
- `dashboard.py`: Streamlit dashboard for interactive analysis
- `INPUT.md`: Original request description
- `README.md`: This file

## Usage

### Testing the Analysis Logic

Run the test script to verify the analysis works:

```bash
uv run src/apps/pre_resolution_analysis/test_analyze_strategy.py
```

### Running the Dashboard

Launch the Streamlit dashboard:

```bash
uv run streamlit run src/apps/pre_resolution_analysis/dashboard.py
```

Then:
1. Adjust parameters in the sidebar (N, X, Y)
2. Click "Run Analysis"
3. Review the results:
   - Key metrics (total markets, qualifying trades, win rate, EV)
   - Pie chart showing win/loss distribution
   - Detailed analysis text
   - Full trade details table
4. Download results as CSV if needed

## Data Source

Data is sourced from the PredictionLabs.Ch Polymarket indexer via ClickHouse.

**Tables used**:
- `polymarket.polymarket_order_filled` - Trade data
- `polymarket.raw_market_meta` - Market metadata and resolution info

## Example Results

For a typical analysis with parameters (N=7, X_min=0.98, X_max=1.00, Y=2):
- **~47,000** resolved markets
- **~17,000** qualifying trades in the price range
- **99.91%** win rate (extremely high confidence signals)
- **Average entry price**: ~0.9975
- **EV**: ~$0.0017 per $1 wagered (0.17% return)

The slight decrease in win rate compared to using last trade price shows that `outcome_price` provides a more accurate, realistic measure of actual profits. Individual trade details help identify which types of markets perform better and when the strategy fails.

## Notes

- Price is calculated as `amount_usdc / amount_token` (both divided by 1e6)
- Only markets with clear resolution outcomes are included
- The strategy assumes you can enter positions at the specified time before resolution
- Historical performance does not guarantee future results

---

*Data from https://predictionlabs.ch*
