# Pumpfun Sniper Analysis - Requirements

## Original Request

Analyze wallet trading activity on Pumpfun to identify "snipe attempts" - trades executed within 20 slots of token creation.

## User Input

- **Wallet Address**: Solana wallet address to analyze

## Analysis Requirements

1. **Fetch Recent Activity**
   - Get 10 most recent Pumpfun BUY transactions for the specified wallet
   - Focus on last 7 days for performance

2. **Identify Snipe Attempts**
   - For each buy, determine if it occurred within 20 slots of token creation
   - A "snipe" is defined as: `0 <= (buy_slot - creation_slot) < 20`

3. **Detailed Transaction Statistics**
   - For each identified snipe attempt, show all transactions in the "snipe window"
   - Snipe window: From token creation to 5 slots after the user's buy
   - Display metrics:
     - Transaction timing (block_time, slot, tx_idx)
     - Wallet addresses involved
     - Trade direction (buy/sell)
     - Gas fees and consumption
     - Tip amounts and recipient addresses

4. **Output Format**
   - Summary statistics (total buys, snipe attempts, snipe rate)
   - Expandable sections for each snipe attempt with detailed trade data
   - CSV download capability for detailed analysis
   - Clear visual presentation in Streamlit dashboard

## Data Sources

- **Database**: ClickHouse at `/root/w3e-research`
- **Tables**:
  - `pumpfun_all_swaps` - Trade data
  - `pumpfun_token_creation` - Token launch data

## Expected Behavior

User enters wallet → App fetches recent buys → Identifies snipes → Displays detailed statistics for each snipe window with transaction-level data including gas and tips.
