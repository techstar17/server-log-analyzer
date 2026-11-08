import argparse
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from nginx_reader import read_nginx_log


parser = argparse.ArgumentParser(
    description="Analyze a CSV file or an Nginx combined access log."
)
parser.add_argument(
    "file",
    type=Path,
    help="Path to a CSV file or an Nginx .log file",
)
args = parser.parse_args()

# Nginx timestamps are converted to UTC by read_nginx_log.
# CSV timestamps stay in the timezone used in the input file.
try:
    if args.file.suffix.lower() == ".log":
        logs = read_nginx_log(args.file)
    else:
        logs = pd.read_csv(args.file)
except (OSError, ValueError, pd.errors.ParserError) as error:
    parser.exit(1, f"Could not read the log file: {error}\n")

# Check the required columns.
required_columns = {"timestamp", "ip", "path", "status"}
missing = required_columns - set(logs.columns)

if missing:
    parser.exit(1, f"Missing columns: {', '.join(sorted(missing))}\n")

if logs.empty:
    parser.exit(1, "The log file has no requests.\n")

# Check that every HTTP status is a whole number from 100 to 599.
logs["status"] = pd.to_numeric(logs["status"], errors="coerce")
valid_status = (
    logs["status"].between(100, 599)
    & logs["status"].mod(1).eq(0)
)

if not valid_status.all():
    parser.exit(1, "Every status must be a whole number from 100 to 599.\n")

logs["status"] = logs["status"].astype(int)

# Validate timestamps before writing reports.
timestamp_format = "%Y-%m-%d %H:%M:%S"
parsed_timestamps = []

for row_number, value in enumerate(logs["timestamp"], start=1):
    try:
        if not isinstance(value, str):
            raise ValueError("Missing timestamp")

        timestamp = datetime.strptime(value, timestamp_format)

        if timestamp.strftime(timestamp_format) != value:
            raise ValueError("Incorrect timestamp format")

    except ValueError:
        parser.exit(
            1,
            f"Invalid timestamp in data row {row_number}. "
            "Use YYYY-MM-DD HH:MM:SS, for example "
            "2026-10-31 10:00:00.\n",
        )

    parsed_timestamps.append(timestamp)

# Calculate the overall results.
total = len(logs)
client_errors = logs["status"].between(400, 499).sum()
server_errors = logs["status"].between(500, 599).sum()
error_rate = (client_errors + server_errors) / total

errors = logs[logs["status"] >= 400]
requests_per_ip = logs["ip"].value_counts()
status_counts = logs["status"].value_counts().sort_index()

# Count requests and errors for each date and hour.
hourly_counts = defaultdict(
    lambda: {
        "requests": 0,
        "client_errors": 0,
        "server_errors": 0,
    }
)

for timestamp, status in zip(parsed_timestamps, logs["status"]):
    hour = timestamp.replace(minute=0, second=0, microsecond=0)
    counts = hourly_counts[hour]
    counts["requests"] += 1

    if 400 <= status <= 499:
        counts["client_errors"] += 1
    elif 500 <= status <= 599:
        counts["server_errors"] += 1

hourly_rows = []

for hour, counts in sorted(hourly_counts.items()):
    total_errors = counts["client_errors"] + counts["server_errors"]

    hourly_rows.append(
        {
            "hour": hour.strftime(timestamp_format),
            "requests": counts["requests"],
            "client_errors": counts["client_errors"],
            "server_errors": counts["server_errors"],
            "total_errors": total_errors,
            "error_rate_percent": total_errors / counts["requests"] * 100,
        }
    )

hourly_report = pd.DataFrame(hourly_rows)

# Display the results.
summary = (
    "SERVER LOG REPORT\n"
    f"File: {args.file}\n"
    f"Total requests: {total}\n"
    f"Client errors (4xx): {client_errors}\n"
    f"Server errors (5xx): {server_errors}\n"
    f"Error rate: {error_rate:.1%}\n"
)

print("\n" + summary)

print("Requests per IP:")
print(requests_per_ip.to_string())

print("\nRequests that returned errors:")
if errors.empty:
    print("No errors found.")
else:
    print(errors[["path", "status"]].to_string(index=False))

print("\nHourly report:")
print(
    hourly_report.to_string(
        index=False,
        formatters={"error_rate_percent": lambda value: f"{value:.1f}%"},
    )
)

# Save the five reports.
report_dir = Path("reports")

try:
    report_dir.mkdir(exist_ok=True)

    (report_dir / "summary.txt").write_text(summary, encoding="utf-8")
    errors.to_csv(report_dir / "errors.csv", index=False)

    requests_per_ip.rename_axis("ip").reset_index(
        name="requests"
    ).to_csv(report_dir / "requests_per_ip.csv", index=False)

    hourly_report.to_csv(
        report_dir / "hourly_report.csv",
        index=False,
        float_format="%.2f",
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    try:
        status_counts.plot(kind="bar", color="steelblue", ax=ax)
        ax.set_title("Requests by HTTP Status")
        ax.set_xlabel("HTTP status code")
        ax.set_ylabel("Number of requests")
        ax.tick_params(axis="x", labelrotation=0)
        fig.tight_layout()
        fig.savefig(report_dir / "status_chart.png", dpi=150)
    finally:
        plt.close(fig)

except OSError as error:
    parser.exit(1, f"Could not save all reports: {error}\n")

print(f"\nReports saved in: {report_dir.resolve()}")
print("  summary.txt")
print("  errors.csv")
print("  requests_per_ip.csv")
print("  hourly_report.csv")
print("  status_chart.png")