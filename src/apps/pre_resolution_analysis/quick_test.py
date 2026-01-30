#!/usr/bin/env python3
"""Quick test with small dataset."""

import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from apps.pre_resolution_analysis.analyze_strategy import analyze_strategy

print("Running quick test with 7 days of data...")
print("Price range: 0.98 - 1.00")
results = analyze_strategy(days_back=7, price_min=0.98, price_max=1.00, minutes_before=2)

print(f"\nResults:")
print(f"Total markets: {results['total_markets']}")
print(f"Qualifying trades: {results['qualifying_trades']}")
print(f"Average entry price: {results['avg_entry_price']:.4f}")
print(f"Wins: {results['wins']}")
print(f"Losses: {results['losses']}")
print(f"Win rate: {results['win_rate']:.2%}")
print(f"Expected Value: ${results['expected_value']:.4f}")
