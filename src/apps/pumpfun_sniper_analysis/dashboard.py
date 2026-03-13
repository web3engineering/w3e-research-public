"""
Streamlit dashboard for Pumpfun sniper analysis.
"""

import sys
import os
import streamlit as st
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.apps.pumpfun_sniper_analysis.analyze_snipers import analyze_wallet_sniping, validate_wallet_address


# Page configuration
st.set_page_config(
    page_title="Pumpfun Sniper Analysis",
    page_icon="🎯",
    layout="wide"
)


def format_sol(lamports: float) -> str:
    """Convert lamports to SOL string."""
    return f"{lamports / 1e9:.6f}"


def main():
    st.title("🎯 Pumpfun Sniper Analysis")
    st.markdown("Analyze wallet trading activity to identify snipe attempts (buys within 20 slots of token creation)")

    # Sidebar
    with st.sidebar:
        st.header("Configuration")

        wallet_address = st.text_input(
            "Wallet Address",
            placeholder="Enter Solana wallet address...",
            help="Solana wallet address (32-44 characters, base58 encoded)"
        )

        num_trades = st.number_input(
            "Number of recent trades",
            min_value=1,
            max_value=50,
            value=10,
            help="Number of recent buy transactions to analyze"
        )

        analyze_button = st.button("Analyze", type="primary", use_container_width=True)

        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This tool identifies "snipe attempts" - trades executed within 20 slots of token creation.

        **Snipe Window**: From token creation to 5 slots after the user's buy.

        **Tip Detection**: Identifies SOL transfers < 0.01 SOL.
        """)

    # Main content area
    if not analyze_button:
        st.info("👈 Enter a wallet address in the sidebar and click 'Analyze' to begin")
        return

    # Validate wallet address
    if not validate_wallet_address(wallet_address):
        st.error("Invalid wallet address. Please enter a valid Solana wallet address (32-44 characters, base58 encoded).")
        return

    # Perform analysis
    with st.spinner(f"Analyzing wallet activity for {wallet_address[:8]}...{wallet_address[-4:]}"):
        try:
            results = analyze_wallet_sniping(wallet_address, limit=num_trades)
        except Exception as e:
            st.error(f"Error analyzing wallet: {str(e)}")
            st.exception(e)
            return

    # Display summary
    summary = results['summary']

    if summary['total_buys'] == 0:
        st.warning("No recent buy transactions found for this wallet in the last 7 days.")
        return

    st.success(f"Analysis complete for {wallet_address[:8]}...{wallet_address[-4:]}")

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Recent Buys", summary['total_buys'])
    with col2:
        st.metric("Snipe Attempts", summary['snipe_attempts'])
    with col3:
        st.metric("Snipe Rate", f"{summary['snipe_rate']:.1f}%")

    st.markdown("---")

    # Display snipe details
    if results['snipe_details']:
        st.header(f"🎯 Snipe Attempts ({len(results['snipe_details'])})")

        for idx, snipe in enumerate(results['snipe_details'], 1):
            with st.expander(
                f"Snipe #{idx} - Token: {snipe['token_mint'][:8]}... "
                f"({snipe['slots_after_creation']} slots after creation)",
                expanded=(idx == 1)  # Expand first snipe by default
            ):
                # Token information
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Token Information**")
                    st.text(f"Mint: {snipe['token_mint']}")
                    st.text(f"Created: {snipe['creation_time']}")
                    st.text(f"Creation Slot: {snipe['creation_slot']} (Tx: {snipe['creation_tx_idx']})")
                with col2:
                    st.markdown("**User Buy Information**")
                    st.text(f"Buy Time: {snipe['user_buy_time']}")
                    st.text(f"Buy Slot: {snipe['user_buy_slot']}")
                    st.text(f"Slots After Creation: {snipe['slots_after_creation']}")

                st.markdown("---")

                # Transaction details table
                trades_df = snipe['window_trades'].copy()

                if not trades_df.empty:
                    st.markdown("**Snipe Window Transactions**")
                    st.caption(f"All trades from token creation to +5 slots after user buy ({len(trades_df)} transactions)")

                    # Format display DataFrame
                    display_df = pd.DataFrame({
                        'Time': trades_df['block_time'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                        'Slot': trades_df['slot'],
                        'TX Idx': trades_df['tx_idx'],
                        'Wallet': trades_df['wallet'].str[:8] + '...',
                        'Side': trades_df['direction'].str.upper(),
                        'Base Amount': trades_df['base_coin_amount'],
                        'Quote Amount': trades_df['quote_coin_amount'],
                        'Gas Fee (SOL)': trades_df['gas_fee'].apply(format_sol),
                        'Gas Units': trades_df['consumed_gas'],
                        'Tips': trades_df['tips'],
                    })

                    # Display with custom column config
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'Time': st.column_config.TextColumn('Time', width='medium'),
                            'Slot': st.column_config.NumberColumn('Slot', format='%d'),
                            'TX Idx': st.column_config.NumberColumn('TX Idx', format='%d'),
                            'Wallet': st.column_config.TextColumn('Wallet', width='small'),
                            'Side': st.column_config.TextColumn('Side', width='small'),
                            'Base Amount': st.column_config.NumberColumn('Base Amount', format='%.2f'),
                            'Quote Amount': st.column_config.NumberColumn('Quote Amount', format='%.2f'),
                            'Gas Fee (SOL)': st.column_config.TextColumn('Gas Fee (SOL)', width='small'),
                            'Gas Units': st.column_config.NumberColumn('Gas Units', format='%d'),
                            'Tips': st.column_config.TextColumn('Tips (account:lamports)', width='medium'),
                        }
                    )

                    # CSV download
                    csv = trades_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"snipe_{snipe['token_mint'][:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key=f"download_snipe_{idx}"
                    )
                else:
                    st.warning("No trades found in snipe window.")

    else:
        st.info("No snipe attempts detected in the recent trades.")

    # Display regular buys (collapsed)
    if not results['regular_buys'].empty:
        st.markdown("---")
        with st.expander(f"📊 Regular Buys ({len(results['regular_buys'])})", expanded=False):
            regular_df = results['regular_buys'].copy()

            display_regular = pd.DataFrame({
                'Time': regular_df['buy_time'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                'Token': regular_df['token_mint'].str[:8] + '...',
                'Slot': regular_df['buy_slot'],
                'Base Amount': regular_df['base_amount'],
                'Quote Amount': regular_df['quote_amount'],
                'Gas Fee (SOL)': regular_df['gas_fee'].apply(format_sol),
            })

            st.dataframe(
                display_regular,
                use_container_width=True,
                hide_index=True
            )


if __name__ == "__main__":
    main()
