# Server Log Analyzer

A Python command-line tool that reads server request data from a CSV file, calculates error rates, and saves reports and a chart.

I built this project to practise Python, log analysis, automated testing, continuous integration, and Docker as part of my DevOps learning.

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
- Runs Python tests and Docker checks through GitHub Actions on every push and pull request.
- Runs locally with Python or inside a Docker container.

## Tools

- Python
- Pandas
- Matplotlib
- unittest
- Git and GitHub
- GitHub Actions
- Docker

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

## Run with Docker on Windows

Start Docker Desktop with Linux containers enabled, then open Command Prompt in the project folder.

The commands below use Windows Command Prompt syntax. Running the Docker image does not require activating the Python virtual environment.

Build the image:

```bat
docker build -t server-log-analyzer:1.0 .
```

Create the output folder:

```bat
if not exist reports mkdir reports
```

Run the analyzer with the second sample dataset:

```bat
docker run --rm --mount "type=bind,source=%cd%\second_logs.csv,target=/data/input.csv,readonly" --mount "type=bind,source=%cd%\reports,target=/app/reports" server-log-analyzer:1.0 /data/input.csv
```

This command:

- Mounts `second_logs.csv` as a read-only input file.
- Saves generated reports in the local `reports` folder.
- Removes the container after it finishes.
- Keeps the reports available on your computer.

The sample produces 10 requests, one client error, one server error, and a 20% error rate.

To use the first sample, replace `second_logs.csv` with `access_logs.csv` in the command.

Open the generated reports:

```bat
start reports
```

Rebuild the image after changing `analyzer.py`, `requirements.txt`, or the `Dockerfile`:

```bat
docker build -t server-log-analyzer:1.0 .
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

Results appear in the terminal. Files are also saved in the `reports` folder within the current working directory.

When using the Docker command above, `/app/reports` inside the container maps to the local `reports` folder.

| File | Contents |
|---|---|
| summary.txt | Input filename, total requests, error counts, and error rate |
| errors.csv | Requests with 4xx or 5xx status codes |
| requests_per_ip.csv | Request count for each IP |
| status_chart.png | Bar chart of requests by status code |

Each run replaces the previous reports.

Open the reports folder on Windows:

```bat
start reports
```

## Automated tests

With the Python dependencies installed, run all tests from the project folder:

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

The workflow in `.github/workflows/tests.yml` runs on GitHub Actions for every push and pull request. It can also be started manually from the Actions tab.

The workflow contains two jobs.

### Python tests

The first job:

1. Checks out the repository.
2. Sets up Python 3.15 on a Linux runner.
3. Installs dependencies from `requirements.txt`.
4. Runs the seven automated tests.

### Docker build and report checks

After the Python tests pass, the second job:

1. Checks out the repository.
2. Builds the Docker image.
3. Runs the analyzer with `second_logs.csv`.
4. Checks that each report heading appears exactly once.
5. Verifies the total requests, error counts, and error rate in the terminal output and saved summary.
6. Checks the error rows and request counts in the generated CSV files.
7. Checks that the chart file has a PNG signature.

Both the Python tests and Docker checks passed on GitHub Actions.

The Docker job builds and tests the image; it does not publish it to a container registry.

[View workflow runs](https://github.com/techstar17/server-log-analyzer/actions)

## Manual checks completed

| Input | Requests | Client errors | Server errors | Error rate |
|---|---:|---:|---:|---:|
| access_logs.csv | 8 | 2 | 2 | 50% |
| second_logs.csv | 10 | 1 | 1 | 20% |

A missing filename was also tested and produced a readable error message.

The Docker container was run locally with `second_logs.csv` and produced the expected counts. After removing duplicated code, the terminal report appeared once.

## Project files

| File | Purpose |
|---|---|
| analyzer.py | Reads the CSV, checks input, and generates reports |
| test_analyzer.py | Automated tests |
| requirements.txt | Pinned Python dependencies |
| access_logs.csv | First sample dataset |
| second_logs.csv | Second sample dataset |
| Dockerfile | Instructions for building the Docker image |
| .dockerignore | Excludes unnecessary files from the Docker build context |
| .gitignore | Excludes the virtual environment and generated files from Git |
| .github/workflows/tests.yml | Python tests and Docker checks on GitHub Actions |
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