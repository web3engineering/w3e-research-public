#!/usr/bin/env python3
"""
Pre-Resolution Trading Strategy Analysis Dashboard

Analyzes a trading strategy where we look at markets Y minutes before resolution,
and check if high-confidence prices (> threshold X) accurately predict the outcome.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from apps.pre_resolution_analysis.analyze_strategy import (
    analyze_strategy,
    format_analysis_text
)


def create_pie_chart(wins: int, losses: int) -> go.Figure:
    """Create a pie chart showing win/loss distribution."""
    fig = go.Figure(data=[go.Pie(
        labels=['Wins', 'Losses'],
        values=[wins, losses],
        hole=0.3,
        marker_colors=['#2ecc71', '#e74c3c'],
        textinfo='label+percent+value',
        textfont_size=16
    )])

    fig.update_layout(
        title={
            'text': 'Win/Loss Distribution',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        showlegend=True,
        height=400
    )

    return fig


def create_details_table(details: list) -> pd.DataFrame:
    """Create a DataFrame with trade details for display."""
    if not details:
        return pd.DataFrame()

    df = pd.DataFrame(details)
    df['question'] = df['question'].str[:80] + '...'
    df['pre_price'] = df['pre_price'].round(4)
    df['outcome_price'] = df['outcome_price'].round(4)
    df['result'] = df['won'].map({True: '✅ Win', False: '❌ Loss'})

    return df[[
        'question',
        'pre_price',
        'outcome_price',
        'outcome',
        'result'
    ]].rename(columns={
        'question': 'Market Question',
        'pre_price': 'Pre-Resolution Price',
        'outcome_price': 'Outcome Price',
        'outcome': 'Outcome',
        'result': 'Result'
    })


def main():
    st.set_page_config(
        page_title="Pre-Resolution Strategy Analysis",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Pre-Resolution Trading Strategy Analysis")
    st.markdown("""
    This dashboard analyzes a trading strategy on Polymarket:
    - Find markets where the price is within a range **[X_min, X_max]** at **Y** minutes before resolution
    - Check how often this high-confidence signal correctly predicts the outcome
    - Calculate the expected value (EV) of this strategy based on actual average entry prices
    """)

    # Sidebar controls
    st.sidebar.header("Strategy Parameters")

    days_back = st.sidebar.slider(
        "Historical Days (N)",
        min_value=1,
        max_value=7,
        value=7,
        step=1,
        help="Number of days of historical data to analyze"
    )

    st.sidebar.subheader("Price Range (X)")

    price_min = st.sidebar.slider(
        "Minimum Price (X_min)",
        min_value=0.90,
        max_value=0.99,
        value=0.98,
        step=0.01,
        help="Minimum price threshold"
    )

    price_max = st.sidebar.slider(
        "Maximum Price (X_max)",
        min_value=0.91,
        max_value=1.00,
        value=1.00,
        step=0.01,
        help="Maximum price threshold"
    )

    if price_min >= price_max:
        st.sidebar.error("X_min must be less than X_max")
        return

    minutes_before = st.sidebar.slider(
        "Minutes Before Resolution (Y)",
        min_value=1,
        max_value=10,
        value=2,
        step=1,
        help="How many minutes before resolution to check the price"
    )

    if st.sidebar.button("🔄 Run Analysis", type="primary"):
        st.session_state['run_analysis'] = True

    # Run analysis
    if 'run_analysis' not in st.session_state:
        st.info("👈 Configure parameters in the sidebar and click 'Run Analysis' to start")
        return

    with st.spinner(f"Analyzing {days_back} days of data..."):
        try:
            results = analyze_strategy(
                days_back=days_back,
                price_min=price_min,
                price_max=price_max,
                minutes_before=minutes_before
            )

            if results['qualifying_trades'] == 0:
                st.warning("No qualifying trades found with the specified parameters. Try adjusting the parameters.")
                return

            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Markets",
                    results['total_markets']
                )

            with col2:
                st.metric(
                    "Qualifying Trades",
                    results['qualifying_trades']
                )

            with col3:
                st.metric(
                    "Win Rate",
                    f"{results['win_rate']:.1%}",
                    delta=f"{results['wins']} wins"
                )

            with col4:
                ev_color = "normal" if results['expected_value'] > 0 else "inverse"
                st.metric(
                    "Expected Value",
                    f"${results['expected_value']:.4f}",
                    delta="per $1 wagered",
                    delta_color=ev_color
                )

            st.divider()

            # Pie chart and analysis
            col_left, col_right = st.columns([1, 1])

            with col_left:
                fig = create_pie_chart(results['wins'], results['losses'])
                st.plotly_chart(fig, use_container_width=True)

            with col_right:
                st.markdown("### Strategy Analysis")
                analysis_text = format_analysis_text(results, price_min, price_max)
                st.markdown(analysis_text)

            # Details table
            st.divider()
            st.markdown("### 📋 Trade Details")

            details_df = create_details_table(results['details'])

            if not details_df.empty:
                st.dataframe(
                    details_df,
                    use_container_width=True,
                    hide_index=True
                )

                # Download button
                csv = details_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name=f"pre_resolution_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

            # Footer
            st.divider()
            st.caption("Data source: https://predictionlabs.ch")

        except Exception as e:
            st.error(f"Error running analysis: {str(e)}")
            import traceback
            with st.expander("Show error details"):
                st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
