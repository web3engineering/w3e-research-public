# Upcoming Events Dashboard

## Original Request

Generate a dashboard with the list of 100 events which will finish soon, sorted by time-to-finish ascending.

## Requirements

1. Consider only active events
2. Sort by time-to-finish (ascending)
3. Display in a table with columns:
   - Name (question)
   - Time to expire
   - Volume 24h
   - Image
4. Important: Handle duplicate metadata rows by picking only the one with the highest `inserted_at` value

## Data Source

- Use `polymarket.raw_market_meta` table
- Filter for `active = TRUE`
- Group by market to handle duplicates, selecting the row with `MAX(inserted_at)`
- Sort by `end_date` ascending
- Limit to 100 results
