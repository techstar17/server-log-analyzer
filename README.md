# Server Log Analyzer

A Python command-line tool that reads server request data from a CSV file, calculates error rates, and saves reports and a chart.

I built this project to practise Python, log analysis, automated testing, and continuous integration as part of my DevOps learning.

## Features

- Counts total requests.
- Counts client errors (4xx) and server errors (5xx).
- Calculates the percentage of requests that returned errors.
- Counts requests from each IP address.
- Lists requests that returned errors.
- Saves a summary, two CSV reports, and a status-code chart.
- Checks for missing columns, empty datasets, and invalid status codes.
- Displays a clear error when an input file cannot be read.
- Includes seven automated tests.
- Runs tests through GitHub Actions on every push and pull request.

## Tools

- Python
- Pandas
- Matplotlib
- unittest
- Git and GitHub
- GitHub Actions

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

To analyze your own CSV file, provide its path:

```bat
python analyzer.py "C:\path\to\your_logs.csv"
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

Results appear in the terminal. Files are also saved in the `reports` folder within the current working directory:

| File | Contents |
|---|---|
| summary.txt | Total requests, error counts, and error rate |
| errors.csv | Requests with 4xx or 5xx status codes |
| requests_per_ip.csv | Request count for each IP |
| status_chart.png | Bar chart of requests by status code |

Each run replaces the previous reports.

Open the reports folder on Windows:

```bat
start reports
```

## Automated tests

Run all tests from the project folder:

```bat
python -m unittest -v
```

The seven tests cover:

1. Request counts, error rates, saved CSV reports, and PNG output.
2. Requests with no errors.
3. A missing input file.
4. An empty file.
5. A CSV containing only column headers.
6. A missing required column.
7. Invalid status codes, including text, missing values, decimals, and out-of-range numbers.

Tests use temporary folders, so they do not overwrite existing reports.

All seven tests passed locally on Windows.

## Continuous integration

The workflow in `.github/workflows/tests.yml` runs on GitHub Actions.

For every push and pull request, it:

1. Checks out the repository.
2. Sets up Python 3.15 on a Linux runner.
3. Installs dependencies from `requirements.txt`.
4. Runs the automated tests.

The workflow can also be started manually from the Actions tab.

The first GitHub Actions run completed successfully.

View workflow runs:
https://github.com/techstar17/server-log-analyzer/actions

## Manual checks completed

| Input | Requests | Client errors | Server errors | Error rate |
|---|---:|---:|---:|---:|
| access_logs.csv | 8 | 2 | 2 | 50% |
| second_logs.csv | 10 | 1 | 1 | 20% |

A missing filename was also tested and produced a readable error message.

## Project files

| File | Purpose |
|---|---|
| analyzer.py | Reads the CSV, checks input, and generates reports |
| test_analyzer.py | Automated tests |
| requirements.txt | Pinned Python dependencies |
| access_logs.csv | First sample dataset |
| second_logs.csv | Second sample dataset |
| .gitignore | Excludes the virtual environment and generated files |
| .github/workflows/tests.yml | GitHub Actions test workflow |
| README.md | Setup and usage instructions |

## Current limits

- Accepts the CSV format above; does not parse raw Nginx or Apache logs.
- Reads the full dataset into memory.
- Requires the timestamp column but does not validate or analyze timestamps.
- Does not validate IP addresses or detect attacks.
- Runs on demand rather than monitoring traffic continuously.
- Overwrites previous reports on each run.

## Planned improvements

- Support for raw web-server logs.
- Requests and errors grouped by time.
- Docker packaging.