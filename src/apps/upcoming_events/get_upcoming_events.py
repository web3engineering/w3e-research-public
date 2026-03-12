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
        DataFrame with columns: market_id, question, market_end_dttm, volume_24hr,
        twitter_card_image, clob_token_id, time_to_expire_seconds
    """
    query = f"""
    SELECT
        t.market_id,
        t.question,
        t.market_end_dttm,
        t.volume_24hr,
        t.twitter_card_image,
        dateDiff('second', now(), t.market_end_dttm) as time_to_expire_seconds
    FROM (
        SELECT
            m.market_id,
            m.question,
            m.market_end_dttm,
            m.volume_24hr,
            m.twitter_card_image,
            m.clob_token_id,
            m.inserted_at,
            ROW_NUMBER() OVER (
                PARTITION BY m.market_id
                ORDER BY m.inserted_at DESC, m.clob_token_id DESC
            ) as rn
        FROM polymarket.raw_market_meta AS m
        WHERE
            m.is_active = TRUE
            AND m.market_end_dttm IS NOT NULL
            AND m.market_end_dttm > now()
    ) t
    WHERE t.rn = 1
    ORDER BY t.market_end_dttm ASC
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
