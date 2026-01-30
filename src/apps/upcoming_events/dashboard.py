"""Streamlit dashboard for upcoming Polymarket events."""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.apps.upcoming_events.get_upcoming_events import (
    get_upcoming_events,
    format_time_to_expire,
    format_volume
)


def main():
    """Main dashboard function."""
    st.set_page_config(
        page_title="Upcoming Polymarket Events",
        page_icon="⏰",
        layout="wide"
    )

    st.title("⏰ Upcoming Polymarket Events")
    st.markdown(
        "This dashboard shows Polymarket events that will finish soon, "
        "sorted by time remaining."
    )

    # Sidebar controls
    with st.sidebar:
        st.header("Settings")
        limit = st.slider(
            "Number of events to display",
            min_value=10,
            max_value=200,
            value=100,
            step=10
        )

        refresh = st.button("🔄 Refresh Data")

    # Fetch data
    with st.spinner("Loading upcoming events..."):
        try:
            df = get_upcoming_events(limit=limit)

            if df.empty:
                st.warning("No upcoming events found.")
                return

            # Add formatted columns
            df['time_remaining'] = df['time_to_expire_seconds'].apply(format_time_to_expire)
            df['volume_formatted'] = df['volume_24hr'].apply(format_volume)

            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Events", len(df))
            with col2:
                total_volume = df['volume_24hr'].sum()
                st.metric("Total 24h Volume", format_volume(total_volume))
            with col3:
                avg_time = df['time_to_expire_seconds'].mean()
                st.metric("Avg Time to Expire", format_time_to_expire(int(avg_time)))

            st.markdown("---")

            # Search filter
            search = st.text_input("🔍 Search events", "")
            if search:
                df = df[df['question'].str.contains(search, case=False, na=False)]
                st.info(f"Showing {len(df)} events matching '{search}'")

            # Display table
            st.subheader(f"Next {len(df)} Events")

            # Create display dataframe
            display_df = pd.DataFrame({
                'Image': df['twitter_card_image'],
                'Question': df['question'],
                'Time to Expire': df['time_remaining'],
                'End Date': df['end_date'].dt.strftime('%Y-%m-%d %H:%M UTC'),
                'Volume 24h': df['volume_formatted'],
            })

            # Use st.dataframe with column configuration for images
            st.dataframe(
                display_df,
                column_config={
                    "Image": st.column_config.ImageColumn(
                        "Image",
                        help="Event image",
                        width="small"
                    ),
                    "Question": st.column_config.TextColumn(
                        "Question",
                        help="Market question",
                        width="large"
                    ),
                    "Time to Expire": st.column_config.TextColumn(
                        "Time to Expire",
                        help="Time remaining until market closes"
                    ),
                    "End Date": st.column_config.TextColumn(
                        "End Date",
                        help="Market end date and time (UTC)"
                    ),
                    "Volume 24h": st.column_config.TextColumn(
                        "Volume 24h",
                        help="Trading volume in last 24 hours"
                    ),
                },
                hide_index=True,
                use_container_width=True,
                height=600
            )

            # Footer with data source
            st.markdown("---")
            st.markdown(
                "<small>Data provided by "
                "[PredictionLabs.ch](https://predictionlabs.ch), [Source Code](https://github.com/web3engineering/w3e-research-public/tree/master/src/apps/upcoming_events)</small>",
                unsafe_allow_html=True
            )

        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.exception(e)


if __name__ == "__main__":
    main()
