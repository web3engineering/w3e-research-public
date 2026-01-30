"""
Analyze pre-resolution trading strategy on Polymarket.

Strategy: Find markets where price was > threshold X at Y minutes before resolution,
and check how often this predicted the final outcome correctly.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
from core.clickhouse import PolymarketAccessor


def get_resolved_markets(days_back: int) -> pd.DataFrame:
    """
    Get markets that resolved in the last N days.

    Args:
        days_back: Number of days to look back

    Returns:
        DataFrame with market metadata including resolution info
    """
    query = """
    WITH latest_meta AS (
        SELECT
            clob_token_id,
            question,
            outcome,
            closed_time,
            parseDateTime64BestEffort(closed_time) as resolution_time,
            argMax(updated_at, updated_at) as latest_update
        FROM polymarket.raw_market_meta
        WHERE outcome IS NOT NULL
          AND outcome != ''
          AND closed_time IS NOT NULL
          AND closed_time != ''
        GROUP BY clob_token_id, question, outcome, closed_time
    )
    SELECT
        clob_token_id as asset,
        question,
        outcome,
        resolution_time
    FROM latest_meta
    WHERE resolution_time IS NOT NULL
      AND resolution_time >= now() - INTERVAL {days} DAY
    ORDER BY resolution_time DESC
    """

    with PolymarketAccessor() as db:
        df = db.query_df(query.format(days=days_back))

    return df


def get_price_before_resolution(
    asset: str,
    resolution_time: datetime,
    minutes_before: int
) -> Tuple[float | None, datetime | None]:
    """
    Get the last trade price Y minutes before resolution.

    Args:
        asset: Token ID
        resolution_time: When the market resolved
        minutes_before: How many minutes before resolution to check

    Returns:
        Tuple of (price, trade_time) or (None, None) if no trades found
    """
    target_time = resolution_time - timedelta(minutes=minutes_before)

    query = """
    SELECT
        amount_usdc / 1e6 as usdc,
        amount_token / 1e6 as tokens,
        (amount_usdc / amount_token) as price,
        block_timestamp
    FROM polymarket.polymarket_order_filled
    WHERE asset = '{asset}'
      AND block_timestamp <= '{target_time}'
      AND amount_token > 0
    ORDER BY block_timestamp DESC
    LIMIT 1
    """

    with PolymarketAccessor() as db:
        result = db.query(query.format(
            asset=asset,
            target_time=target_time.strftime('%Y-%m-%d %H:%M:%S')
        ))

    if result:
        return result[0]['price'], result[0]['block_timestamp']
    return None, None


def get_final_price(asset: str, resolution_time: datetime) -> float | None:
    """
    Get the last trade price at or near resolution time.

    Args:
        asset: Token ID
        resolution_time: When the market resolved

    Returns:
        Final price or None if no trades found
    """
    query = """
    SELECT
        (amount_usdc / amount_token) as price,
        block_timestamp
    FROM polymarket.polymarket_order_filled
    WHERE asset = '{asset}'
      AND block_timestamp <= '{resolution_time}'
      AND amount_token > 0
    ORDER BY block_timestamp DESC
    LIMIT 1
    """

    with PolymarketAccessor() as db:
        result = db.query(query.format(
            asset=asset,
            resolution_time=resolution_time.strftime('%Y-%m-%d %H:%M:%S')
        ))

    if result:
        return result[0]['price']
    return None


def analyze_strategy(
    days_back: int = 7,
    price_min: float = 0.98,
    price_max: float = 1.00,
    minutes_before: int = 2
) -> Dict:
    """
    Analyze the pre-resolution trading strategy using an optimized query.

    Args:
        days_back: Number of days of historical data to analyze
        price_min: Minimum price threshold (e.g., 0.98)
        price_max: Maximum price threshold (e.g., 1.00)
        minutes_before: Minutes before resolution to check price

    Returns:
        Dictionary with analysis results including win rate and EV
    """
    # Optimized query that gets everything in one go
    query = """
    WITH resolved_markets AS (
        SELECT
            clob_token_id as asset,
            question,
            outcome,
            outcome_price,
            parseDateTime64BestEffort(closed_time) as resolution_time
        FROM (
            SELECT
                clob_token_id,
                question,
                outcome,
                outcome_price,
                closed_time,
                row_number() OVER (PARTITION BY clob_token_id ORDER BY updated_at DESC) as rn
            FROM polymarket.raw_market_meta
            WHERE outcome IS NOT NULL
              AND outcome != ''
              AND outcome_price IS NOT NULL
              AND outcome_price != ''
              AND closed_time IS NOT NULL
              AND closed_time != ''
        )
        WHERE rn = 1
          AND parseDateTime64BestEffort(closed_time) >= now() - INTERVAL {days} DAY
          AND parseDateTime64BestEffort(closed_time) IS NOT NULL
    ),
    pre_resolution_prices AS (
        SELECT
            f.asset,
            m.question,
            m.outcome,
            m.outcome_price,
            m.resolution_time,
            argMax(f.amount_usdc / f.amount_token, f.block_timestamp) as pre_price,
            max(f.block_timestamp) as pre_time
        FROM polymarket.polymarket_order_filled f
        INNER JOIN resolved_markets m ON f.asset = m.asset
        WHERE f.block_timestamp <= m.resolution_time - INTERVAL {minutes} MINUTE
          AND f.amount_token > 0
        GROUP BY f.asset, m.question, m.outcome, m.outcome_price, m.resolution_time
        HAVING pre_price > {price_min} AND pre_price < {price_max}
    )
    SELECT
        asset,
        question,
        outcome,
        CAST(outcome_price AS Float64) as outcome_price,
        resolution_time,
        pre_price,
        pre_time
    FROM pre_resolution_prices
    ORDER BY resolution_time DESC
    """

    with PolymarketAccessor() as db:
        df = db.query_df(query.format(
            days=days_back,
            minutes=minutes_before,
            price_min=price_min,
            price_max=price_max
        ))

    if len(df) == 0:
        # Get total markets count
        total_markets_query = """
        SELECT COUNT(DISTINCT clob_token_id) as count
        FROM (
            SELECT
                clob_token_id,
                parseDateTime64BestEffort(closed_time) as resolution_time,
                row_number() OVER (PARTITION BY clob_token_id ORDER BY updated_at DESC) as rn
            FROM polymarket.raw_market_meta
            WHERE outcome IS NOT NULL
              AND outcome != ''
              AND closed_time IS NOT NULL
              AND closed_time != ''
        )
        WHERE rn = 1
          AND resolution_time >= now() - INTERVAL {days} DAY
        """
        with PolymarketAccessor() as db:
            result = db.query(total_markets_query.format(days=days_back))
            total_markets = result[0]['count'] if result else 0

        return {
            'total_markets': total_markets,
            'qualifying_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'expected_value': 0,
            'avg_entry_price': 0,
            'details': []
        }

    # Determine wins and losses
    # Win if outcome_price >= minimum threshold (market resolved to YES/high probability)
    df['won'] = df['outcome_price'] >= price_min

    qualifying_trades = []
    for _, row in df.iterrows():
        qualifying_trades.append({
            'asset': row['asset'],
            'question': row['question'],
            'pre_price': float(row['pre_price']),
            'pre_time': row['pre_time'],
            'outcome_price': float(row['outcome_price']),
            'resolution_time': row['resolution_time'],
            'outcome': row['outcome'],
            'won': row['won']
        })

    wins = int(df['won'].sum())
    losses = len(df) - wins
    win_rate = wins / len(df)

    # EV calculation using average entry price
    avg_entry_price = df['pre_price'].mean()
    # When you win, you gain (1.0 - avg_entry_price)
    # When you lose, you lose avg_entry_price
    expected_value = win_rate * (1.0 - avg_entry_price) - (1 - win_rate) * avg_entry_price

    # Get total markets count
    total_markets_query = """
    SELECT COUNT(DISTINCT clob_token_id) as count
    FROM (
        SELECT
            clob_token_id,
            parseDateTime64BestEffort(closed_time) as resolution_time,
            row_number() OVER (PARTITION BY clob_token_id ORDER BY updated_at DESC) as rn
        FROM polymarket.raw_market_meta
        WHERE outcome IS NOT NULL
          AND outcome != ''
          AND closed_time IS NOT NULL
          AND closed_time != ''
    )
    WHERE rn = 1
      AND resolution_time >= now() - INTERVAL {days} DAY
    """
    with PolymarketAccessor() as db:
        result = db.query(total_markets_query.format(days=days_back))
        total_markets = result[0]['count'] if result else len(df)

    return {
        'total_markets': total_markets,
        'qualifying_trades': len(qualifying_trades),
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'expected_value': expected_value,
        'avg_entry_price': avg_entry_price,
        'details': qualifying_trades
    }


def format_analysis_text(results: Dict, price_min: float, price_max: float) -> str:
    """
    Format analysis results into readable text.

    Args:
        results: Results dictionary from analyze_strategy
        price_min: Minimum price threshold used
        price_max: Maximum price threshold used

    Returns:
        Formatted analysis text
    """
    if results['qualifying_trades'] == 0:
        return "No qualifying trades found in the specified time period."

    win_rate = results['win_rate']
    wins = results['wins']
    losses = results['losses']
    total = results['qualifying_trades']
    ev = results['expected_value']
    avg_price = results.get('avg_entry_price', (price_min + price_max) / 2)

    gain_per_win = 1.0 - avg_price
    loss_per_loss = avg_price

    text = f"""
**Strategy Analysis Results**

Out of {results['total_markets']} resolved markets, found {total} qualifying trades
where price was between {price_min:.2f} and {price_max:.2f} at the specified time before resolution.

**Average Entry Price**: {avg_price:.4f}
**Win Rate**: {win_rate:.2%} ({wins} wins out of {total} trades)

**Probability Interpretation**:
In {int(win_rate * 100)} cases out of 100, you win ${gain_per_win:.4f} per $1 wagered.
In {int((1 - win_rate) * 100)} cases out of 100, you lose ${loss_per_loss:.4f} per $1 wagered.

**Expected Value (EV)**: ${ev:.4f} per $1 wagered
{f"This strategy has a **positive** expected value of {ev:.2%}." if ev > 0 else f"This strategy has a **negative** expected value of {ev:.2%}."}

**Interpretation**:
- For every $100 wagered using this strategy, you can expect to {"gain" if ev > 0 else "lose"} ${abs(ev * 100):.2f} on average.
"""

    return text
