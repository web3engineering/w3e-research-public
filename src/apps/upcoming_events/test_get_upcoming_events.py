"""Test script for upcoming events helper functions."""

from get_upcoming_events import (
    get_upcoming_events,
    format_time_to_expire,
    format_volume
)


def test_format_time_to_expire():
    """Test time formatting function."""
    print("Testing format_time_to_expire:")
    test_cases = [
        (0, "< 1m"),
        (30, "< 1m"),
        (3600, "1h"),
        (7200, "2h"),
        (86400, "1d"),
        (90000, "1d 1h"),
        (93600, "1d 2h"),
        (93660, "1d 2h 1m"),
        (-100, "Expired"),
    ]

    for seconds, expected in test_cases:
        result = format_time_to_expire(seconds)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {seconds}s -> {result} (expected: {expected})")


def test_format_volume():
    """Test volume formatting function."""
    print("\nTesting format_volume:")
    test_cases = [
        (0, "$0"),
        (500, "$500"),
        (1_500, "$1.5K"),
        (50_000, "$50.0K"),
        (1_200_000, "$1.2M"),
        (5_500_000, "$5.5M"),
        (None, "$0"),
    ]

    for volume, expected in test_cases:
        result = format_volume(volume)
        status = "✓" if result == expected else "✗"
        print(f"  {status} ${volume} -> {result} (expected: {expected})")


def test_get_upcoming_events():
    """Test fetching upcoming events from database."""
    print("\nTesting get_upcoming_events:")
    print("Fetching 10 upcoming events...")

    try:
        df = get_upcoming_events(limit=10)
        print(f"✓ Successfully fetched {len(df)} events")
        print("\nColumns:", list(df.columns))
        print("\nFirst 3 events:")
        print(df[['question', 'end_date', 'volume_24hr', 'time_to_expire_seconds']].head(3))

        # Apply formatting
        print("\nFormatted output:")
        for idx, row in df.head(3).iterrows():
            print(f"\n{idx + 1}. {row['question']}")
            print(f"   Time to expire: {format_time_to_expire(row['time_to_expire_seconds'])}")
            print(f"   Volume 24h: {format_volume(row['volume_24hr'])}")
            print(f"   End date: {row['end_date']}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_format_time_to_expire()
    test_format_volume()
    test_get_upcoming_events()
