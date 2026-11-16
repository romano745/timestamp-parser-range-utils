# timestamp-parser-range-utils

Parse ISO 8601 timestamps with optional fractional seconds and UTC offset, and
optionally enforce an inclusive time range.

```python
from datetime import datetime, timezone
from timestamp_parser_range_utils import parse_timestamp, parse_timestamp_range

stamp = parse_timestamp("2024-01-02T03:04:05.123Z")
assert stamp == datetime(2024, 1, 2, 3, 4, 5, 123000, tzinfo=timezone.utc)

start = datetime(2024, 1, 1, tzinfo=timezone.utc)
end = datetime(2024, 1, 3, tzinfo=timezone.utc)
parse_timestamp_range("2024-01-02T00:00:00Z", start, end)
```

## Why this exists

Most timestamp parsers accept too much. They quietly interpret `2024-01` as a
year and month, or `2024-01-02T03:04:05,5Z` with a comma decimal separator, and
then produce a datetime that does not match what the caller meant. This library
accepts exactly one shape:

```
YYYY-MM-DDTHH:MM:SS[.fraction][Z|+HH:MM|-HH:MM]
```

Anything else raises `ValueError`. That is a trade-off: you cannot parse week
dates or ordinal dates, but a typo in a log line fails loudly instead of being
silently coerced.

## Awkward edge

When the UTC offset is omitted, the result is treated as UTC. This is the
common convention for API and log payloads, but it is not what ISO 8601
requires. If your data is local time without an offset, parse it with an
explicit offset before passing it in.

## API

- `parse_timestamp(value: str) -> datetime` — parse a compliant string into a
timezone-aware `datetime`. Fractional seconds beyond six digits are truncated,
not rounded.
- `parse_timestamp_range(value: str, start: datetime | None = None, end: datetime | None = None) -> datetime` — parse and assert the result is within
  the inclusive `[start, end]` range. Naive bounds are interpreted as UTC.
- `TimestampRangeError` — raised by `parse_timestamp_range` when the parsed
  timestamp is outside the bounds. It subclasses `ValueError`.
