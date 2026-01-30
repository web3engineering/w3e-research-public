"""Helper module to fetch upcoming Polymarket events."""

import pandas as pd
from datetime import datetime
from src.core.clickhouse import PolymarketAccessor


def get_upcoming_events(limit: int = 100) -> pd.DataFrame:
    """Fetch upcoming Polymarket events sorted by end date.

    Fetches active events that will finish soon, handling duplicate metadata
    rows by selecting the most recently inserted row for each market.

    Args:
        limit: Maximum number of events to return (default: 100)

    Returns:
        DataFrame with columns: id, question, end_date, volume_24hr,
        twitter_card_image, clob_token_id, time_to_expire_seconds
    """
    query = f"""
    WITH latest_meta AS (
        SELECT
            id,
            question,
            end_date,
            volume_24hr,
            twitter_card_image,
            clob_token_id,
            inserted_at,
            ROW_NUMBER() OVER (
                PARTITION BY id
                ORDER BY inserted_at DESC, clob_token_id DESC
            ) as rn
        FROM polymarket.raw_market_meta
        WHERE
            active = TRUE
            AND end_date IS NOT NULL
            AND end_date > now()
    )
    SELECT DISTINCT
        id,
        question,
        end_date,
        volume_24hr,
        twitter_card_image,
        dateDiff('second', now(), end_date) as time_to_expire_seconds
    FROM latest_meta
    WHERE rn = 1
    ORDER BY end_date ASC
    LIMIT {limit}
    """

    with PolymarketAccessor() as db:
        df = db.query_df(query)

    return df


def format_time_to_expire(seconds: int) -> str:
    """Format seconds into a human-readable string.

    Args:
        seconds: Number of seconds

    Returns:
        Formatted string like "2d 5h 30m" or "5h 30m" or "30m"
    """
    if seconds < 0:
        return "Expired"

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")

    return " ".join(parts) if parts else "< 1m"


def format_volume(volume: float) -> str:
    """Format volume in a readable format.

    Args:
        volume: Volume value in dollars

    Returns:
        Formatted string like "$1.2M" or "$450K"
    """
    if volume is None or pd.isna(volume):
        return "$0"

    if volume >= 1_000_000:
        return f"${volume / 1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"${volume / 1_000:.1f}K"
    else:
        return f"${volume:.0f}"
