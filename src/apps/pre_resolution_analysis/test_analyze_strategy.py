#!/usr/bin/env python3
"""
Test script for pre-resolution strategy analysis.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from apps.pre_resolution_analysis.analyze_strategy import (
    analyze_strategy,
    format_analysis_text,
    get_resolved_markets
)


def main():
    print("Testing Pre-Resolution Strategy Analysis\n")
    print("=" * 60)

    # Test 1: Get resolved markets
    print("\n1. Fetching resolved markets from last 7 days...")
    try:
        markets = get_resolved_markets(days_back=7)
        print(f"   Found {len(markets)} resolved markets")
        if len(markets) > 0:
            print(f"   Sample market: {markets.iloc[0]['question'][:80]}...")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Run strategy analysis with default parameters
    print("\n2. Running strategy analysis (default parameters)...")
    print("   Days back: 7")
    print("   Price range: 0.98 - 1.00")
    print("   Minutes before resolution: 2")

    try:
        results = analyze_strategy(
            days_back=7,
            price_min=0.98,
            price_max=1.00,
            minutes_before=2
        )

        print(f"\n   Results:")
        print(f"   - Total markets analyzed: {results['total_markets']}")
        print(f"   - Qualifying trades: {results['qualifying_trades']}")
        print(f"   - Average entry price: {results.get('avg_entry_price', 'N/A')}")
        print(f"   - Wins: {results['wins']}")
        print(f"   - Losses: {results['losses']}")
        print(f"   - Win rate: {results['win_rate']:.2%}")
        print(f"   - Expected Value: ${results['expected_value']:.4f}")

        if results['qualifying_trades'] > 0:
            print(f"\n   Sample qualifying trades:")
            for i, trade in enumerate(results['details'][:3], 1):
                print(f"   {i}. {trade['question'][:60]}...")
                print(f"      Pre-price: {trade['pre_price']:.4f}, Outcome: {trade['outcome_price']:.4f}, Won: {trade['won']}")

    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Format analysis text
    print("\n3. Formatted analysis text:")
    print("-" * 60)
    try:
        text = format_analysis_text(results, 0.98, 1.00)
        print(text)
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    main()
