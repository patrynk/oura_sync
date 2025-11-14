#!/usr/bin/env python3
"""Test script to validate mappers with existing JSON data."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.mappers import (
    map_daily_activity,
    map_daily_sleep,
    map_daily_readiness,
    map_daily_spo2,
    map_daily_stress,
)


def test_mapper(mapper_func, json_file: Path, data_type: str):
    """Test a mapper function with JSON data."""
    print(f"\n{'='*80}")
    print(f"Testing {data_type} mapper")
    print(f"{'='*80}")

    if not json_file.exists():
        print(f"❌ File not found: {json_file}")
        return False

    try:
        # Load JSON data
        with open(json_file) as f:
            data_list = json.load(f)

        print(f"✓ Loaded {len(data_list)} records from {json_file.name}")

        # Test mapping first record
        if not data_list:
            print("⚠ No records to test")
            return True

        test_user_id = "test_user_123"
        first_record = data_list[0]

        print(f"\nTesting first record:")
        print(f"  ID: {first_record.get('id')}")
        print(f"  Day: {first_record.get('day')}")

        # Map the record
        mapped = mapper_func(first_record, test_user_id)

        print(f"\n✓ Mapping successful!")
        print(f"  Mapped ID: {mapped.id}")
        print(f"  Mapped day: {mapped.day}")
        print(f"  User ID: {mapped.user_id}")

        # Show some mapped fields
        print(f"\nSample mapped fields:")
        for key, value in mapped.__dict__.items():
            if not key.startswith("_") and key not in ["raw_data", "id", "user_id"]:
                print(f"  {key}: {value}")
                if len([k for k in mapped.__dict__.keys() if not k.startswith("_")]) > 10:
                    break

        print(f"\n✓ {data_type} mapper test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ {data_type} mapper test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all mapper tests."""
    print("\n" + "="*80)
    print("MAPPER VALIDATION TESTS")
    print("="*80)

    data_dir = Path(__file__).parent.parent / "data"

    tests = [
        (map_daily_sleep, data_dir / "daily_sleep" / "2025-11-05_to_2025-11-12.json", "daily_sleep"),
        (map_daily_readiness, data_dir / "daily_readiness" / "2025-11-05_to_2025-11-12.json", "daily_readiness"),
        (map_daily_spo2, data_dir / "daily_spo2" / "2025-11-05_to_2025-11-12.json", "daily_spo2"),
        (map_daily_stress, data_dir / "daily_stress" / "2025-11-05_to_2025-11-12.json", "daily_stress"),
        (map_daily_activity, data_dir / "daily_activity" / "2025-11-05_to_2025-11-12.json", "daily_activity"),
    ]

    results = []
    for mapper, json_file, data_type in tests:
        result = test_mapper(mapper, json_file, data_type)
        results.append((data_type, result))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for data_type, result in results:
        status = "✓ PASSED" if result else "❌ FAILED"
        print(f"{status}: {data_type}")

    all_passed = all(result for _, result in results)

    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
