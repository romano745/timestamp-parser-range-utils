"""Core parsing logic for ISO 8601 timestamps.

The parser accepts a deliberately restricted subset of ISO 8601:

    YYYY-MM-DDTHH:MM:SS[.fraction][Z|+HH:MM|-HH:MM]

Why restrict it?
    ISO 8601 permits week dates, ordinal dates, comma decimal separators, and
    reduced precision (e.g. ``2024-01``). Supporting all of those makes it
    impossible to distinguish a typo from a valid-but-unusual timestamp. This
    library targets the common RFC 3339-like form used by APIs and logs, and
    raises ``ValueError`` for everything else so callers notice immediately.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

__all__ = ["parse_timestamp", "TimestampRangeError", "parse_timestamp_range"]


class TimestampRangeError(ValueError):
    """Raised when a timestamp falls outside an allowed range."""


# The regex is intentionally strict. It anchors both ends, requires exactly
# four digits for the year, and only allows the colon-separated offset form.
_TIMESTAMP_RE = re.compile(
    r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
    r"T"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
    r"(?:\.(?P<fraction>\d{1,9}))?"
    r"(?P<offset>Z|[+-]\d{2}:\d{2})?$"
)


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 timestamp into a timezone-aware ``datetime``.

    Fractional seconds are truncated to microseconds (six digits). The input
    must include a date, time, and seconds. An offset is optional; when it is
    omitted the result is treated as UTC, matching the common convention in
    log and API payloads.

    Raises:
        ValueError: if ``value`` is not a string, does not match the accepted
            format, or contains a calendar-invalid date/time.
    """
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")

    match = _TIMESTAMP_RE.match(value)
    if match is None:
        raise ValueError(f"timestamp is not ISO 8601 compliant: {value!r}")

    parts = match.groupdict()

    # ``fraction`` is optional. Pad or truncate to exactly six digits so
    # ``datetime`` can consume it as microseconds. Truncation is deliberate:
    # nanosecond precision is lost rather than rounded, which keeps parsing
    # monotonic with respect to the input string.
    fraction = parts["fraction"] or ""
    microsecond = int(fraction.ljust(6, "0")[:6]) if fraction else 0

    offset_text = parts["offset"]
    if offset_text is None or offset_text == "Z":
        tzinfo = timezone.utc
    else:
        sign = 1 if offset_text[0] == "+" else -1
        offset_hours = int(offset_text[1:3])
        offset_minutes = int(offset_text[4:6])
        if offset_hours > 23 or offset_minutes > 59:
            raise ValueError(f"UTC offset out of range: {offset_text!r}")
        tzinfo = timezone(sign * timedelta(hours=offset_hours, minutes=offset_minutes))

    try:
        return datetime(
            year=int(parts["year"]),
            month=int(parts["month"]),
            day=int(parts["day"]),
            hour=int(parts["hour"]),
            minute=int(parts["minute"]),
            second=int(parts["second"]),
            microsecond=microsecond,
            tzinfo=tzinfo,
        )
    except ValueError as exc:
        # Re-raise with the offending value so callers can log it directly.
        raise ValueError(f"invalid calendar date/time in {value!r}: {exc}") from exc


def parse_timestamp_range(
    value: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> datetime:
    """Parse ``value`` and assert it falls within ``[start, end]``.

    The bounds are inclusive. Either bound may be ``None`` to leave that side
    unbounded. Naive bounds are interpreted as UTC so that comparison never
    raises ``TypeError`` from mixing aware and naive datetimes.

    Returns:
        The parsed, timezone-aware ``datetime``.

    Raises:
        ValueError: if ``value`` cannot be parsed.
        TimestampRangeError: if the parsed timestamp is outside the bounds.
    """
    parsed = parse_timestamp(value)

    # Normalise naive bounds to UTC. This is a deliberate choice: the parser
    # always returns aware datetimes, so accepting naive bounds without a
    # convention would force every caller to remember ``replace(tzinfo=utc)``.
    if start is not None and start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end is not None and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    if start is not None and parsed < start:
        raise TimestampRangeError(
            f"timestamp {value!r} is before the allowed start {start.isoformat()}"
        )
    if end is not None and parsed > end:
        raise TimestampRangeError(
            f"timestamp {value!r} is after the allowed end {end.isoformat()}"
        )

    return parsed
