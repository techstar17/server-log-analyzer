# Server Log Analyzer

A Python command-line tool that reads CSV request data or Nginx combined access logs. It shows which requests failed, how often each IP appeared, and how error rates changed by hour.

I built this project to practise Python, log analysis, automated testing, Docker, and continuous integration as part of my DevOps learning.

## Run on Windows

Open Command Prompt in the project folder. The project was tested with Python 3.15.

Create a virtual environment and install the dependencies:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Run either sample:

```bat
python analyzer.py second_logs.csv
```

```bat
python analyzer.py sample_nginx.log
```

To analyze your own file, pass its path:

```bat
python analyzer.py "C:\logs\access.log"
```

## Supported input

### CSV request data

The CSV must include `timestamp`, `ip`, `path`, and `status`:

```csv
timestamp,ip,path,status
2026-10-31 10:00:00,192.0.2.20,/,200
2026-10-31 10:01:00,192.0.2.21,/missing,404
```

Use the timestamp format `YYYY-MM-DD HH:MM:SS` and the same timezone throughout the file. CSV reports use the times supplied in the input. Status codes must be whole numbers from 100 to 599.

### Nginx combined access logs

Use a filename ending in `.log`. The analyzer expects the Nginx combined access log format, with one request per line:

```text
192.0.2.21 - - [31/Oct/2026:11:00:00 +0100] "GET /missing HTTP/1.1" 404 128 "-" "sample-client"
```

The analyzer reads the IP, timestamp, request path, and HTTP status. It converts the timestamp to UTC before grouping requests. For example, the request above appears in the `10:00 UTC` hour. If a line does not match the expected format, the analyzer reports its line number.

## Reports

Results appear in the terminal. Each successful run writes five files to the `reports` folder and replaces the previous results.

| File | Contents |
|---|---|
| `summary.txt` | Input filename, total requests, client errors, server errors, and overall error rate |
| `errors.csv` | Requests with a 4xx or 5xx status |
| `requests_per_ip.csv` | Request count for each IP |
| `hourly_report.csv` | Requests, client errors, server errors, total errors, and error rate for each hour with traffic |
| `status_chart.png` | Bar chart showing the number of requests for each HTTP status code |

Open the reports folder in Windows:

```bat
start reports
```

## Sample results

The included files contain made-up requests for testing.

| Sample | Requests | Client errors (4xx) | Server errors (5xx) | Error rate |
|---|---:|---:|---:|---:|
| `access_logs.csv` | 8 | 2 | 2 | 50.0% |
| `second_logs.csv` | 10 | 1 | 1 | 20.0% |
| `sample_nginx.log` | 3 | 1 | 1 | 66.7% |

The Nginx sample contains two different timezone offsets. After conversion to UTC, its hourly report is:

```csv
hour,requests,client_errors,server_errors,total_errors,error_rate_percent
2026-10-31 09:00:00,1,0,0,0,0.00
2026-10-31 10:00:00,2,1,1,2,100.00
```

## Run with Docker on Windows

Start Docker Desktop with Linux containers enabled. From the project folder in **Command Prompt**, build the image and create an output folder:

```bat
docker build -t server-log-analyzer:1.2 .
if not exist reports\nginx-docker mkdir reports\nginx-docker
```

Run the Nginx sample:

```bat
docker run --rm --mount "type=bind,source=%cd%\sample_nginx.log,target=/data/input.log,readonly" --mount "type=bind,source=%cd%\reports\nginx-docker,target=/app/reports" server-log-analyzer:1.2 /data/input.log
```

The input mount is read-only. The reports remain in `reports\nginx-docker` on Windows after the container exits. View the hourly CSV:

```bat
type reports\nginx-docker\hourly_report.csv
```

To run the CSV sample in Docker, use a `.csv` filename inside the container and a separate output folder:

```bat
if not exist reports\csv-docker mkdir reports\csv-docker
docker run --rm --mount "type=bind,source=%cd%\second_logs.csv,target=/data/input.csv,readonly" --mount "type=bind,source=%cd%\reports\csv-docker,target=/app/reports" server-log-analyzer:1.2 /data/input.csv
```

## Testing and continuous integration

Run all 11 tests from the project folder:

```bat
.venv\Scripts\python.exe -m unittest -v
```

| Test file | Coverage |
|---|---|
| `test_analyzer.py` | Summary counts, saved reports, requests with no errors, missing files and columns, empty input, and invalid status codes |
| `test_hourly.py` | Hourly counts and error rates across dates, chronological ordering, and invalid timestamps |
| `test_nginx.py` | Nginx input through the command line, UTC grouping, error paths and statuses, and line numbers for malformed input |

All 11 tests passed locally on Windows. The Nginx sample was also run in Docker, and the saved hourly CSV matched the expected UTC counts.

On pushes and pull requests, GitHub Actions runs the Python tests on Linux. After they pass, a second job builds the Docker image, runs the CSV sample, and checks its output. [View workflow runs](https://github.com/techstar17/server-log-analyzer/actions)

## Current limits

- The Nginx reader expects the combined access log format. Custom log formats need a different parser.
- CSV timestamps must use one timezone. Nginx timestamps include offsets and are converted to UTC.
- The analyzer reads the dataset into memory and runs on demand.
- IP counts and HTTP errors describe traffic. They do not establish whether a request was an attack.