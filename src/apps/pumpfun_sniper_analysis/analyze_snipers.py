"""
Core analysis logic for identifying and analyzing Pumpfun snipe attempts.
"""

import sys
import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.core.clickhouse import ClickHouseAccessor


def get_recent_buys(wallet: str, limit: int = 10) -> pd.DataFrame:
    """
    Fetch the most recent buy transactions for a wallet on Pumpfun.

    Args:
        wallet: Solana wallet address
        limit: Number of recent buys to fetch (default 10)

    Returns:
        DataFrame with columns: token_mint, buy_slot, buy_tx_idx, buy_time,
                                base_amount, quote_amount, gas_fee, gas_consumed
    """
    query = """
    SELECT
        toString(base_coin) as token_mint,
        slot as buy_slot,
        tx_idx as buy_tx_idx,
        block_time as buy_time,
        base_coin_amount as base_amount,
        quote_coin_amount as quote_amount,
        provided_gas_fee as gas_fee,
        consumed_gas as gas_consumed
    FROM pumpfun_all_swaps
    WHERE toString(signing_wallet) = %(wallet)s
      AND direction = 'buy'
      AND block_time >= now() - INTERVAL 7 DAY
    ORDER BY block_time DESC
    LIMIT %(limit)s
    """

    with ClickHouseAccessor() as db:
        df = db.query_df(query, {'wallet': wallet, 'limit': limit})

    return df


def get_token_creation_info(token_mints: List[str]) -> Dict[str, Dict]:
    """
    Batch fetch token creation information for multiple tokens.

    Args:
        token_mints: List of token mint addresses

    Returns:
        Dict mapping mint -> {creation_slot, creation_tx_idx, creation_time}
    """
    if not token_mints:
        return {}

    query = """
    SELECT
        toString(mint) as token_mint,
        slot as creation_slot,
        tx_idx as creation_tx_idx,
        block_time as creation_time
    FROM pumpfun_token_creation
    WHERE toString(mint) IN %(mints)s
    """

    with ClickHouseAccessor() as db:
        results = db.query(query, {'mints': token_mints})

    # Convert to dict for easy lookup
    return {
        row['token_mint']: {
            'creation_slot': row['creation_slot'],
            'creation_tx_idx': row['creation_tx_idx'],
            'creation_time': row['creation_time']
        }
        for row in results
    }


def is_snipe_attempt(buy_slot: int, creation_slot: int) -> bool:
    """
    Determine if a buy is a snipe attempt (within 20 slots of creation).

    Args:
        buy_slot: Slot number of the buy transaction
        creation_slot: Slot number of token creation

    Returns:
        True if this is a snipe attempt (0 <= slots_after < 20)
    """
    slots_after = buy_slot - creation_slot
    return 0 <= slots_after < 20


def get_snipe_window_trades(
    token_mint: str,
    creation_slot: int,
    creation_tx_idx: int,
    user_buy_slot: int,
    user_buy_tx_idx: int
) -> pd.DataFrame:
    """
    Fetch all trades in the snipe window for a token.

    Snipe window: From token creation to 5 slots after user's buy.

    Args:
        token_mint: Token mint address
        creation_slot: Slot of token creation
        creation_tx_idx: TX index of token creation
        user_buy_slot: Slot of user's buy
        user_buy_tx_idx: TX index of user's buy

    Returns:
        DataFrame with all trades in the window, ordered by slot/tx_idx
    """
    end_slot = user_buy_slot + 5

    query = """
    SELECT
        block_time,
        slot,
        tx_idx,
        toString(signing_wallet) as wallet,
        direction,
        base_coin_amount,
        quote_coin_amount,
        provided_gas_fee as gas_fee,
        consumed_gas,
        top_level_transfers_json
    FROM pumpfun_all_swaps
    WHERE toString(base_coin) = %(token_mint)s
      AND (
        (slot = %(creation_slot)s AND tx_idx >= %(creation_tx_idx)s)
        OR (slot > %(creation_slot)s AND slot < %(end_slot)s)
        OR (slot = %(end_slot)s AND tx_idx <= %(user_buy_tx_idx)s)
      )
    ORDER BY slot ASC, tx_idx ASC
    """

    with ClickHouseAccessor() as db:
        df = db.query_df(query, {
            'token_mint': token_mint,
            'creation_slot': creation_slot,
            'creation_tx_idx': creation_tx_idx,
            'end_slot': end_slot,
            'user_buy_tx_idx': user_buy_tx_idx
        })

    return df


def parse_tip_data(transfers_json: str) -> List[Dict]:
    """
    Parse top-level transfers JSON to identify tips (transfers < 0.01 SOL).

    Args:
        transfers_json: JSON string containing transfer data

    Returns:
        List of tip dictionaries with 'to', 'amount_lamports', 'amount_sol'
    """
    if not transfers_json or transfers_json == '[]':
        return []

    try:
        transfers = json.loads(transfers_json)

        # Identify tips: transfers < 0.01 SOL (< 10,000,000 lamports)
        tips = []
        for transfer in transfers:
            # The field is called 'lamports' and it's a string, so convert to int
            amount_lamports_str = transfer.get('lamports', '0')
            try:
                amount_lamports = int(amount_lamports_str)
            except (ValueError, TypeError):
                continue

            if 0 < amount_lamports < 10_000_000:  # Between 0 and 0.01 SOL
                tips.append({
                    'to': transfer.get('to', 'unknown'),
                    'amount_lamports': amount_lamports,
                    'amount_sol': amount_lamports / 1e9
                })

        return tips
    except (json.JSONDecodeError, TypeError, KeyError):
        return []


def format_tips_for_display(tips: List[Dict]) -> str:
    """
    Format tip data for display in DataFrame.

    Args:
        tips: List of tip dictionaries

    Returns:
        Combined string in format "account:amount,account:amount"
    """
    if not tips:
        return ''

    formatted_tips = [f"{tip['to'][:8]}...:{tip['amount_lamports']}" for tip in tips]
    return ','.join(formatted_tips)


def analyze_wallet_sniping(wallet: str, limit: int = 10) -> Dict:
    """
    Perform complete sniping analysis for a wallet.

    Args:
        wallet: Solana wallet address
        limit: Number of recent buys to analyze

    Returns:
        Dict with 'summary' and 'snipe_details' keys containing analysis results
    """
    # Step 1: Fetch recent buys
    recent_buys = get_recent_buys(wallet, limit)

    if recent_buys.empty:
        return {
            'summary': {
                'total_buys': 0,
                'snipe_attempts': 0,
                'snipe_rate': 0.0
            },
            'snipe_details': [],
            'regular_buys': pd.DataFrame()
        }

    # Step 2: Get token creation info for all tokens
    token_mints = recent_buys['token_mint'].unique().tolist()
    creation_info = get_token_creation_info(token_mints)

    # Step 3: Identify snipe attempts
    snipe_details = []
    regular_buys = []

    for _, buy in recent_buys.iterrows():
        token_mint = buy['token_mint']
        buy_slot = buy['buy_slot']

        # Check if we have creation info for this token
        if token_mint not in creation_info:
            regular_buys.append(buy)
            continue

        creation = creation_info[token_mint]
        creation_slot = creation['creation_slot']

        # Check if this is a snipe attempt
        if is_snipe_attempt(buy_slot, creation_slot):
            slots_after = buy_slot - creation_slot

            # Fetch detailed trades in snipe window
            window_trades = get_snipe_window_trades(
                token_mint=token_mint,
                creation_slot=creation_slot,
                creation_tx_idx=creation['creation_tx_idx'],
                user_buy_slot=buy['buy_slot'],
                user_buy_tx_idx=buy['buy_tx_idx']
            )

            # Parse tips for each trade
            if not window_trades.empty:
                window_trades['tips'] = window_trades['top_level_transfers_json'].apply(
                    lambda x: format_tips_for_display(parse_tip_data(x))
                )

            snipe_details.append({
                'token_mint': token_mint,
                'creation_time': creation['creation_time'],
                'creation_slot': creation_slot,
                'creation_tx_idx': creation['creation_tx_idx'],
                'user_buy_time': buy['buy_time'],
                'user_buy_slot': buy_slot,
                'slots_after_creation': slots_after,
                'window_trades': window_trades
            })
        else:
            regular_buys.append(buy)

    # Step 4: Compile summary
    total_buys = len(recent_buys)
    snipe_attempts = len(snipe_details)
    snipe_rate = (snipe_attempts / total_buys * 100) if total_buys > 0 else 0.0

    return {
        'summary': {
            'total_buys': total_buys,
            'snipe_attempts': snipe_attempts,
            'snipe_rate': snipe_rate
        },
        'snipe_details': snipe_details,
        'regular_buys': pd.DataFrame(regular_buys) if regular_buys else pd.DataFrame()
    }


def validate_wallet_address(wallet: str) -> bool:
    """
    Validate Solana wallet address format.

    Args:
        wallet: Wallet address to validate

    Returns:
        True if valid format (32-44 chars, base58)
    """
    if not wallet or len(wallet) < 32 or len(wallet) > 44:
        return False

    # Basic base58 character check
    base58_chars = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
    return all(c in base58_chars for c in wallet)
