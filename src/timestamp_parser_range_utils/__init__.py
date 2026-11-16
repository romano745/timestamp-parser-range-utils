"""Timestamp Parser Range utilities.

This package parses ISO 8601 timestamps that may include fractional seconds and
an optional UTC offset. It deliberately rejects ambiguous or non-compliant
strings by raising ``ValueError``.
"""

from .core import parse_timestamp, TimestampRangeError, parse_timestamp_range

__all__ = ["parse_timestamp", "TimestampRangeError", "parse_timestamp_range"]
