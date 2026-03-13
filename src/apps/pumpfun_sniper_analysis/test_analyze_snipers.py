"""
Test script for sniper analysis functions.
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.apps.pumpfun_sniper_analysis.analyze_snipers import (
    is_snipe_attempt,
    parse_tip_data,
    format_tips_for_display,
    validate_wallet_address
)


def test_is_snipe_attempt():
    """Test snipe detection logic."""
    print("Testing is_snipe_attempt()...")

    # Test cases: (buy_slot, creation_slot, expected_result)
    test_cases = [
        (1000, 1000, True, "Same slot"),
        (1005, 1000, True, "5 slots after"),
        (1019, 1000, True, "19 slots after (edge case)"),
        (1020, 1000, False, "20 slots after (not a snipe)"),
        (1050, 1000, False, "50 slots after"),
        (995, 1000, False, "Before creation (invalid)"),
    ]

    all_passed = True
    for buy_slot, creation_slot, expected, description in test_cases:
        result = is_snipe_attempt(buy_slot, creation_slot)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"  {status} {description}: buy={buy_slot}, creation={creation_slot}, result={result}")

    print(f"\nis_snipe_attempt: {'All tests passed!' if all_passed else 'Some tests failed'}\n")


def test_parse_tip_data():
    """Test tip parsing from JSON."""
    print("Testing parse_tip_data()...")

    # Test case 1: Valid tips
    transfers_json1 = json.dumps([
        {"to": "TipAccount1", "amount": 5000000},  # 0.005 SOL (tip)
        {"to": "TipAccount2", "amount": 1000000},  # 0.001 SOL (tip)
        {"to": "LargeTransfer", "amount": 50000000},  # 0.05 SOL (not a tip)
    ])
    tips1 = parse_tip_data(transfers_json1)
    print(f"  Test 1 - Valid tips: {len(tips1)} tips found")
    for tip in tips1:
        print(f"    - {tip['to']}: {tip['amount_sol']:.6f} SOL ({tip['amount_lamports']} lamports)")

    # Test case 2: No tips
    transfers_json2 = json.dumps([
        {"to": "Account1", "amount": 100000000},  # 0.1 SOL (not a tip)
    ])
    tips2 = parse_tip_data(transfers_json2)
    print(f"  Test 2 - No tips: {len(tips2)} tips found")

    # Test case 3: Empty array
    tips3 = parse_tip_data("[]")
    print(f"  Test 3 - Empty array: {len(tips3)} tips found")

    # Test case 4: Invalid JSON
    tips4 = parse_tip_data("invalid json")
    print(f"  Test 4 - Invalid JSON: {len(tips4)} tips found (should handle gracefully)")

    print()


def test_format_tips_for_display():
    """Test tip formatting for display."""
    print("Testing format_tips_for_display()...")

    # Test case 1: Multiple tips
    tips1 = [
        {"to": "TipAccount123456", "amount_lamports": 5000000, "amount_sol": 0.005},
        {"to": "TipAccount789012", "amount_lamports": 1000000, "amount_sol": 0.001},
    ]
    accounts1, amounts1 = format_tips_for_display(tips1)
    print(f"  Test 1 - Multiple tips:")
    print(f"    Accounts: {accounts1}")
    print(f"    Amounts: {amounts1}")

    # Test case 2: No tips
    accounts2, amounts2 = format_tips_for_display([])
    print(f"  Test 2 - No tips:")
    print(f"    Accounts: '{accounts2}' (should be empty)")
    print(f"    Amounts: '{amounts2}' (should be empty)")

    print()


def test_validate_wallet_address():
    """Test wallet address validation."""
    print("Testing validate_wallet_address()...")

    test_cases = [
        ("5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1", True, "Valid address"),
        ("", False, "Empty string"),
        ("short", False, "Too short"),
        ("a" * 50, False, "Too long"),
        ("InvalidChars!@#$%^&*()", False, "Invalid characters"),
        ("1111111111111111111111111111111111", True, "Valid base58"),
    ]

    all_passed = True
    for address, expected, description in test_cases:
        result = validate_wallet_address(address)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        display_addr = address[:20] + "..." if len(address) > 20 else address
        print(f"  {status} {description}: '{display_addr}' -> {result}")

    print(f"\nvalidate_wallet_address: {'All tests passed!' if all_passed else 'Some tests failed'}\n")


def test_analyze_wallet_sniping():
    """
    Test full wallet analysis (commented out by default - requires DB connection).

    Uncomment and provide a real wallet address to test against live database.
    """
    print("Testing analyze_wallet_sniping()...")
    print("  Skipped - requires database connection")
    print("  To test: uncomment code below and provide a wallet address\n")

    # Uncomment to test with real data:
    # from src.apps.pumpfun_sniper_analysis.analyze_snipers import analyze_wallet_sniping
    # wallet = "YOUR_WALLET_ADDRESS_HERE"
    # results = analyze_wallet_sniping(wallet, limit=5)
    # print(f"  Total buys: {results['summary']['total_buys']}")
    # print(f"  Snipe attempts: {results['summary']['snipe_attempts']}")
    # print(f"  Snipe rate: {results['summary']['snipe_rate']:.1f}%")


if __name__ == "__main__":
    print("=" * 60)
    print("Pumpfun Sniper Analysis - Unit Tests")
    print("=" * 60)
    print()

    test_is_snipe_attempt()
    test_parse_tip_data()
    test_format_tips_for_display()
    test_validate_wallet_address()
    test_analyze_wallet_sniping()

    print("=" * 60)
    print("Tests complete!")
    print("=" * 60)
