import unittest
from datetime import datetime, timezone, timedelta

from timestamp_parser_range_utils import (
    parse_timestamp,
    parse_timestamp_range,
    TimestampRangeError,
)


class ParseTimestampTests(unittest.TestCase):
    def test_utc_z_suffix(self):
        got = parse_timestamp("2024-01-02T03:04:05Z")
        self.assertEqual(got, datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc))

    def test_missing_offset_is_utc(self):
        got = parse_timestamp("2024-01-02T03:04:05")
        self.assertEqual(got.tzinfo, timezone.utc)

    def test_positive_offset(self):
        got = parse_timestamp("2024-01-02T03:04:05+05:30")
        expected = datetime(
            2024, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=5, minutes=30))
        )
        self.assertEqual(got, expected)

    def test_negative_offset(self):
        got = parse_timestamp("2024-01-02T03:04:05-08:00")
        expected = datetime(
            2024, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=-8))
        )
        self.assertEqual(got, expected)

    def test_fractional_seconds_padded(self):
        got = parse_timestamp("2024-01-02T03:04:05.5Z")
        self.assertEqual(got.microsecond, 500000)

    def test_fractional_seconds_truncated_to_microseconds(self):
        got = parse_timestamp("2024-01-02T03:04:05.123456789Z")
        self.assertEqual(got.microsecond, 123456)

    def test_rejects_non_string(self):
        with self.assertRaises(ValueError):
            parse_timestamp(20240102)

    def test_rejects_ambiguous_date_only(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2024-01-02")

    def test_rejects_comma_fraction(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2024-01-02T03:04:05,5Z")

    def test_rejects_invalid_calendar_date(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2023-02-29T00:00:00Z")

    def test_rejects_offset_out_of_range(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2024-01-02T03:04:05+24:00")

    def test_rejects_short_year(self):
        with self.assertRaises(ValueError):
            parse_timestamp("24-01-02T03:04:05Z")

    def test_rejects_trailing_junk(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2024-01-02T03:04:05Z extra")


class ParseTimestampRangeTests(unittest.TestCase):
    def test_within_bounds(self):
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 3, tzinfo=timezone.utc)
        got = parse_timestamp_range("2024-01-02T00:00:00Z", start, end)
        self.assertEqual(got, datetime(2024, 1, 2, tzinfo=timezone.utc))

    def test_bounds_are_inclusive(self):
        start = datetime(2024, 1, 2, tzinfo=timezone.utc)
        end = datetime(2024, 1, 2, tzinfo=timezone.utc)
        got = parse_timestamp_range("2024-01-02T00:00:00Z", start, end)
        self.assertEqual(got, start)

    def test_before_start_raises(self):
        start = datetime(2024, 1, 2, tzinfo=timezone.utc)
        with self.assertRaises(TimestampRangeError):
            parse_timestamp_range("2024-01-01T00:00:00Z", start=start)

    def test_after_end_raises(self):
        end = datetime(2024, 1, 2, tzinfo=timezone.utc)
        with self.assertRaises(TimestampRangeError):
            parse_timestamp_range("2024-01-03T00:00:00Z", end=end)

    def test_naive_bounds_are_utc(self):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 3)
        got = parse_timestamp_range("2024-01-02T00:00:00Z", start, end)
        self.assertEqual(got.tzinfo, timezone.utc)

    def test_unbounded_sides(self):
        got = parse_timestamp_range("2024-01-02T00:00:00Z")
        self.assertEqual(got, datetime(2024, 1, 2, tzinfo=timezone.utc))

    def test_parse_error_propagates(self):
        with self.assertRaises(ValueError):
            parse_timestamp_range("not-a-timestamp")


if __name__ == "__main__":
    unittest.main()
