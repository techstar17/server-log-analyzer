import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser(
    description="Analyze a CSV server log and save reports."
)
parser.add_argument("file", type=Path, help="Path to the CSV log file")
args = parser.parse_args()

# Read the CSV file.
try:
    logs = pd.read_csv(args.file)
except (OSError, ValueError, pd.errors.ParserError) as error:
    parser.exit(1, f"Could not read the log file: {error}\n")

# Validate the required columns.
required_columns = {"timestamp", "ip", "path", "status"}
missing = required_columns - set(logs.columns)

if missing:
    parser.exit(1, f"Missing columns: {', '.join(sorted(missing))}\n")

if logs.empty:
    parser.exit(1, "The log file has no requests.\n")

# Validate HTTP status codes.
logs["status"] = pd.to_numeric(logs["status"], errors="coerce")
valid_status = (
    logs["status"].between(100, 599)
    & logs["status"].mod(1).eq(0)
)

if not valid_status.all():
    parser.exit(
        1,
        "Every status must be a whole number from 100 to 599.\n",
    )

logs["status"] = logs["status"].astype(int)

# Calculate the results.
total = len(logs)
client_errors = logs["status"].between(400, 499).sum()
server_errors = logs["status"].between(500, 599).sum()
error_rate = (client_errors + server_errors) / total

errors = logs[logs["status"] >= 400]
requests_per_ip = logs["ip"].value_counts()
status_counts = logs["status"].value_counts().sort_index()

summary = (
    "SERVER LOG REPORT\n"
    f"File: {args.file}\n"
    f"Total requests: {total}\n"
    f"Client errors (4xx): {client_errors}\n"
    f"Server errors (5xx): {server_errors}\n"
    f"Error rate: {error_rate:.1%}\n"
)

# Display each section once.
print("\n" + summary)

print("Requests per IP:")
print(requests_per_ip.to_string())

print("\nRequests that returned errors:")
if errors.empty:
    print("No errors found.")
else:
    print(errors[["path", "status"]].to_string(index=False))

# Save reports and the chart.
report_dir = Path("reports")

try:
    report_dir.mkdir(exist_ok=True)

    (report_dir / "summary.txt").write_text(
        summary,
        encoding="utf-8",
    )

    errors.to_csv(report_dir / "errors.csv", index=False)

    requests_per_ip.rename_axis("ip").reset_index(
        name="requests"
    ).to_csv(report_dir / "requests_per_ip.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    status_counts.plot(kind="bar", color="steelblue", ax=ax)

    ax.set_title("Requests by HTTP Status")
    ax.set_xlabel("HTTP status code")
    ax.set_ylabel("Number of requests")
    ax.tick_params(axis="x", labelrotation=0)

    fig.tight_layout()
    fig.savefig(report_dir / "status_chart.png", dpi=150)
    plt.close(fig)

except OSError as error:
    parser.exit(1, f"Could not save all reports: {error}\n")

print(f"\nReports saved in: {report_dir.resolve()}")
print("  summary.txt")
print("  errors.csv")
print("  requests_per_ip.csv")
print("  status_chart.png")