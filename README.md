# Server Log Analyzer

A Python command-line tool that reads server request data from a CSV file, calculates error rates, and saves reports and a chart.

I built this project to practise Python, data analysis, and working with logs as part of my DevOps learning.

## Features

- Counts total requests.
- Counts client errors (4xx) and server errors (5xx).
- Calculates the percentage of requests that returned errors.
- Counts requests from each IP address.
- Lists requests that returned errors.
- Saves a summary, two CSV reports, and a status-code chart.
- Checks for missing columns, empty datasets, and invalid status codes.
- Displays a clear error when an input file cannot be read.

## Tools

- Python
- Pandas
- Matplotlib
- Git

## Setup on Windows

Download or clone this repository, then open Command Prompt in the project folder.

Create and activate a virtual environment:

```bat
py -m venv .venv
.venv\Scripts\activate
```

Install the dependencies:

```bat
python -m pip install -r requirements.txt
```

## Usage

Run the analyzer with one of the included sample files:

```bat
python analyzer.py access_logs.csv
```

Or:

```bat
python analyzer.py second_logs.csv
```

## Input format

The CSV must contain these columns:

```csv
timestamp,ip,path,status
2026-10-31 10:00:00,192.0.2.20,/,200
2026-10-31 10:01:00,192.0.2.21,/missing,404
```

Status codes must be whole numbers from 100 to 599.

The included datasets are made-up examples, not production traffic.

## Output

Results appear in the terminal. Files are also saved in the `reports` folder:

| File | Contents |
|---|---|
| summary.txt | Total requests, error counts, and error rate |
| errors.csv | Requests with 4xx or 5xx status codes |
| requests_per_ip.csv | Request count for each IP |
| status_chart.png | Bar chart of requests by status code |

Each run replaces the previous reports.

## Manual checks completed

| Input | Requests | Client errors | Server errors | Error rate |
|---|---:|---:|---:|---:|
| access_logs.csv | 8 | 2 | 2 | 50% |
| second_logs.csv | 10 | 1 | 1 | 20% |

A missing filename was also tested and produced a readable error message.

## Current limits

- Accepts the CSV format above; does not parse raw Nginx or Apache logs.
- Reads the full dataset into memory.
- Requires the timestamp column but does not validate or analyze timestamps.
- Does not validate IP addresses or detect attacks.
- Runs on demand rather than monitoring traffic continuously.

## Planned improvements

- Automated tests.
- Support for raw web-server logs.
- Requests and errors grouped by time.
- Docker packaging.