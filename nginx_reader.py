import re
from datetime import datetime, timedelta, timezone

import pandas as pd


# Combined format: IP, identity, user, time, request, status,
# bytes sent, referrer, and user agent.
LOG_LINE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<request>(?:\\.|[^"\\])*)" '
    r'(?P<status>[0-9]{3}) (?:[0-9]+|-) '
    r'"(?:\\.|[^"\\])*" "(?:\\.|[^"\\])*"$'
)

LOG_TIME = re.compile(
    r"(\d{2})/([A-Za-z]{3})/(\d{4}):"
    r"(\d{2}):(\d{2}):(\d{2}) ([+-])(\d{2})(\d{2})"
)

MONTHS = {
    name: number
    for number, name in enumerate(
        "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), start=1
    )
}


def utc_timestamp(value):
    match = LOG_TIME.fullmatch(value)
    if not match:
        raise ValueError("invalid Nginx timestamp")

    day, month, year, hour, minute, second, sign, offset_h, offset_m = (
        match.groups()
    )
    month_number = MONTHS.get(month)
    if month_number is None or int(offset_h) > 23 or int(offset_m) > 59:
        raise ValueError("invalid month or timezone offset")

    offset = timedelta(hours=int(offset_h), minutes=int(offset_m))
    if sign == "-":
        offset = -offset

    timestamp = datetime(
        int(year), month_number, int(day),
        int(hour), int(minute), int(second),
        tzinfo=timezone(offset),
    )
    return timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def read_nginx_log(path):
    rows = []

    with path.open(encoding="utf-8") as log_file:
        for line_number, line in enumerate(log_file, start=1):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue

            match = LOG_LINE.fullmatch(line)
            if not match:
                raise ValueError(
                    f"Line {line_number}: expected Nginx combined log format."
                )

            try:
                timestamp = utc_timestamp(match["time"])
            except (ValueError, OverflowError) as error:
                raise ValueError(
                    f"Line {line_number}: invalid timestamp {match['time']!r}."
                ) from error

            # Nginx can log "-" when no request line was available.
            request_parts = match["request"].split()
            request_path = request_parts[1] if len(request_parts) >= 2 else "-"

            rows.append((timestamp, match["ip"], request_path, match["status"]))

    return pd.DataFrame(rows, columns=["timestamp", "ip", "path", "status"])