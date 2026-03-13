# Pumpfun Sniper Analysis

Analyze wallet trading activity on Pumpfun to identify "snipe attempts" - trades executed within 20 slots of token creation.

## Purpose

This tool helps identify wallets that attempt to buy tokens very early after their creation on Pumpfun. For each snipe attempt, it provides detailed transaction-level statistics including timing, gas fees, and tip amounts.

## Usage

From the repository root:

```bash
cd /root/w3e-research-public
uv run streamlit run src/apps/pumpfun_sniper_analysis/dashboard.py
```

Or use the launcher script:

```bash
./src/apps/pumpfun_sniper_analysis/run.sh
```

## Input

- **Wallet Address**: Solana wallet address to analyze (32-44 characters, base58 encoded)

## Output

### Summary Metrics
- Total recent buys analyzed
- Number of snipe attempts identified
- Snipe rate percentage

### Detailed Snipe Statistics
For each snipe attempt:
- Token information (mint address, creation time)
- User's buy timing (time, slots after creation)
- Complete transaction table showing:
  - Time, Slot, TX Index
  - Wallet addresses
  - Trade direction (buy/sell)
  - Gas fees (SOL) and gas units consumed
  - Tip accounts and amounts (SOL)
- CSV download option

### Regular Buys
- Collapsed section showing non-snipe trades

## Database Schema Notes

### pumpfun_all_swaps
- `signing_wallet`: Trader wallet address
- `direction`: 'buy' or 'sell'
- `base_coin`: Token mint address
- `slot`, `tx_idx`: Transaction position
- `provided_gas_fee`, `consumed_gas`: Gas metrics
- `top_level_transfers_json`: JSON array of SOL transfers (for tip detection)

### pumpfun_token_creation
- `mint`: Token address
- `slot`, `tx_idx`: Creation position
- `block_time`: Creation timestamp

## Definitions

- **Snipe Attempt**: A buy transaction that occurs within 20 slots of token creation
- **Snipe Window**: From token creation to 5 slots after the user's buy
- **Tip**: SOL transfers < 0.01 SOL (< 10,000,000 lamports)

## Testing

Run unit tests from repository root:
```bash
cd /root/w3e-research-public
uv run python src/apps/pumpfun_sniper_analysis/test_analyze_snipers.py
```

## Technical Notes

- Analyzes last 7 days of activity for performance
- SOL amounts use 9 decimal places (lamports / 1e9)
- Handles slot/tx_idx boundaries for precise window filtering
- Graceful error handling for missing data or malformed JSON
