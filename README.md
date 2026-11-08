# Server Log Analyzer

A Python command-line tool that reads server requests from a CSV file and shows how often they returned errors. It reports totals for the whole file and for each hour, then saves a summary, three CSV reports, and a chart.

I built this project to practise Python, log analysis, automated testing, Docker, and continuous integration as part of my DevOps learning.

## Features

- Counts total requests, client errors (4xx), and server errors (5xx).
- Calculates the percentage of requests that returned errors.
- Counts requests from each IP address.
- Lists the requests that returned errors, including their paths and status codes.
- Groups requests and errors by date and hour.
- Checks for unreadable files, missing columns, empty datasets, invalid status codes, and invalid timestamps.
- Runs locally with Python or inside a Docker container.

## Tools

Python, pandas, Matplotlib, unittest, Docker, Git, GitHub, and GitHub Actions.

## Setup on Windows

Download or clone this repository and open Command Prompt in the project folder. The project was tested with Python 3.15.

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

Run the analyzer with either sample file:

```bat
python analyzer.py access_logs.csv
```

```bat
python analyzer.py second_logs.csv
```

To analyze your own file, pass its path:

```bat
python analyzer.py "C:\path\to\your_logs.csv"
```

## Run with Docker on Windows

Start Docker Desktop with Linux containers enabled. Open **Command Prompt** in the project folder. You can run the Docker version without activating the Python virtual environment.

Build the image:

```bat
docker build -t server-log-analyzer:1.1 .
```

Create the folder for the reports:

```bat
if not exist reports mkdir reports
```

Run the analyzer:

```bat
docker run --rm --mount "type=bind,source=%cd%\second_logs.csv,target=/data/input.csv,readonly" --mount "type=bind,source=%cd%\reports,target=/app/reports" server-log-analyzer:1.1 /data/input.csv
```

The container reads `second_logs.csv` and writes the reports to the `reports` folder on your computer. The reports remain available after the container exits.

To use `access_logs.csv`, replace `second_logs.csv` in the input mount. Rebuild the image after changing `analyzer.py`, `requirements.txt`, or the `Dockerfile`.

## Input format

The CSV must include these four columns:

```csv
timestamp,ip,path,status
2026-10-31 10:00:00,192.0.2.20,/,200
2026-10-31 10:01:00,192.0.2.21,/missing,404
```

- `timestamp` must be a valid date and time in `YYYY-MM-DD HH:MM:SS` format. Include leading zeros and use the same timezone throughout the file.
- `status` must be a whole number from 100 to 599.

If a timestamp is invalid, the analyzer stops before writing reports and identifies the affected data row. Data row 1 is the first request after the header.

The included CSV files contain made-up requests for testing.

## Output

Results appear in the terminal. The analyzer also writes five files to `reports` in the current working directory. Each successful run replaces the previous reports.

| File | Contents |
|---|---|
| `summary.txt` | Input filename, total requests, client errors, server errors, and overall error rate |
| `errors.csv` | Input rows with a 4xx or 5xx status code |
| `requests_per_ip.csv` | Request count for each IP address |
| `hourly_report.csv` | Request count, client errors, server errors, total errors, and error rate for each hour with traffic |
| `status_chart.png` | Bar chart showing the number of requests for each HTTP status code |

Open the reports folder on Windows:

```bat
start reports
```

### Reading the hourly report

The analyzer lists hours in date and time order. A request at `10:59:59` belongs to the `10:00:00` hour. A request at `11:00:00` starts the next hour. The same hour on two different dates gets two separate rows. Hours with no requests are omitted.

For `second_logs.csv`, the hourly CSV contains:

```csv
hour,requests,client_errors,server_errors,total_errors,error_rate_percent
2026-10-31 10:00:00,10,1,1,2,20.00
```

During that hour, 2 of the 10 requests returned errors: one client error and one server error. The `20.00` value means 20% of requests in that hour returned an error.

## Automated tests

With the virtual environment active, run the test suite from the project folder:

```bat
python -m unittest -v
```

All nine tests passed locally on Windows. They cover:

1. Request totals, error rates, saved CSV reports, and PNG output.
2. Requests with no errors.
3. A missing input file.
4. An empty file.
5. A CSV containing only column headers.
6. A missing required column.
7. Invalid status codes.
8. Hourly counts, error rates, and chronological order across hours and dates.
9. Invalid timestamps, including missing values, impossible dates, and incorrect formats.

The tests use temporary folders so they can check generated files without overwriting your reports.

## Continuous integration

The [GitHub Actions workflow](.github/workflows/tests.yml) runs on pushes and pull requests. It can also be started manually from the Actions tab.

1. **Python tests:** A Linux runner sets up Python 3.15, installs the dependencies, and runs all nine tests. The hourly tests check the contents of `hourly_report.csv` and how the analyzer handles invalid timestamps.
2. **Docker build and report checks:** After the Python tests pass, a second job builds the image and runs it with `second_logs.csv`. It checks the original report headings for duplicate output, verifies the overall counts and error rate, checks the error rows and per-IP counts, and verifies the chart file’s PNG signature.

Both jobs passed for the hourly reporting update. [View workflow runs](https://github.com/techstar17/server-log-analyzer/actions)

## Manual checks

| Input | Requests | Client errors | Server errors | Overall error rate |
|---|---:|---:|---:|---:|
| `access_logs.csv` | 8 | 2 | 2 | 50% |
| `second_logs.csv` | 10 | 1 | 1 | 20% |

Running the analyzer with a missing filename produced a readable error message. Running `second_logs.csv` produced one hourly row because all ten sample requests occurred within the same hour.

## Project files

| File | Purpose |
|---|---|
| `analyzer.py` | Reads and validates the input, calculates results, and saves reports |
| `test_analyzer.py` | Tests request counts, report files, status codes, and input errors |
| `test_hourly.py` | Tests hourly grouping, error rates, and timestamp validation |
| `requirements.txt` | Lists the pinned Python dependencies |
| `access_logs.csv` | Sample dataset with eight requests |
| `second_logs.csv` | Sample dataset with ten requests |
| `Dockerfile` | Builds the analyzer image |
| `.dockerignore` | Excludes unnecessary files from the Docker build |
| `.gitignore` | Excludes the virtual environment and generated reports from Git |
| `.github/workflows/tests.yml` | Runs the Python tests and Docker checks on GitHub Actions |
| `README.md` | Explains setup, usage, reports, and tests |

## Current limits

- Accepts CSV input in the format shown above. Raw Nginx and Apache logs need to be converted first.
- Reads the full dataset into memory.
- Expects timestamps in one timezone and does not convert between timezones.
- Counts requests by the supplied IP value without validating IP addresses.
- Runs on demand and does not monitor live traffic or detect attacks.
- Replaces earlier reports when run from the same working directory.

## Planned improvement

- Add support for raw web-server logs.