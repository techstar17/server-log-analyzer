import csv
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ANALYZER = Path(__file__).resolve().parent / "analyzer.py"
HEADER = "timestamp,ip,path,status\n"


class AnalyzerTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.work_dir = Path(self.temp_dir.name)

    def run_analyzer(self, content=None):
        input_file = self.work_dir / "test_logs.csv"

        if content is not None:
            input_file.write_text(content, encoding="utf-8")

        environment = os.environ.copy()
        environment["MPLBACKEND"] = "Agg"

        return subprocess.run(
            [sys.executable, str(ANALYZER), str(input_file)],
            cwd=self.work_dir,
            capture_output=True,
            text=True,
            env=environment,
            timeout=60,
        )

    def test_counts_and_saved_reports(self):
        data = HEADER + (
            "2026-11-01 10:00:00,192.0.2.10,/,200\n"
            "2026-11-01 10:01:00,192.0.2.10,/login,200\n"
            "2026-11-01 10:02:00,192.0.2.11,/missing,404\n"
            "2026-11-01 10:03:00,192.0.2.12,/api,500\n"
        )

        result = self.run_analyzer(data)

        self.assertEqual(result.returncode, 0, result.stderr)

        reports = self.work_dir / "reports"
        summary = (reports / "summary.txt").read_text(
            encoding="utf-8"
        )

        for expected in (
            "Total requests: 4",
            "Client errors (4xx): 1",
            "Server errors (5xx): 1",
            "Error rate: 50.0%",
        ):
            self.assertIn(expected, result.stdout)
            self.assertIn(expected, summary)

        with (reports / "errors.csv").open(
            encoding="utf-8", newline=""
        ) as file:
            errors = list(csv.DictReader(file))

        self.assertEqual(len(errors), 2)
        self.assertEqual(
            {(row["path"], row["status"]) for row in errors},
            {("/missing", "404"), ("/api", "500")},
        )

        with (reports / "requests_per_ip.csv").open(
            encoding="utf-8", newline=""
        ) as file:
            counts = {
                row["ip"]: int(row["requests"])
                for row in csv.DictReader(file)
            }

        self.assertEqual(
            counts,
            {"192.0.2.10": 2, "192.0.2.11": 1, "192.0.2.12": 1},
        )

        chart = (reports / "status_chart.png").read_bytes()
        self.assertTrue(chart.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_no_errors(self):
        data = HEADER + (
            "2026-11-01 10:00:00,192.0.2.10,/,200\n"
            "2026-11-01 10:01:00,192.0.2.11,/old,301\n"
        )

        result = self.run_analyzer(data)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Error rate: 0.0%", result.stdout)
        self.assertIn("No errors found.", result.stdout)

        with (self.work_dir / "reports" / "errors.csv").open(
            encoding="utf-8", newline=""
        ) as file:
            self.assertEqual(list(csv.DictReader(file)), [])

    def assert_rejected(self, result, message):
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((self.work_dir / "reports").exists())

    def test_missing_file(self):
        result = self.run_analyzer()

        self.assert_rejected(
            result,
            "Could not read the log file",
        )

    def test_empty_file(self):
        result = self.run_analyzer("")

        self.assert_rejected(
            result,
            "Could not read the log file",
        )

    def test_header_without_requests(self):
        result = self.run_analyzer(HEADER)

        self.assert_rejected(
            result,
            "The log file has no requests.",
        )

    def test_missing_column(self):
        data = (
            "timestamp,ip,path\n"
            "2026-11-01 10:00:00,192.0.2.10,/\n"
        )

        result = self.run_analyzer(data)

        self.assert_rejected(
            result,
            "Missing columns: status",
        )

    def test_invalid_status_codes(self):
        for status in ("oops", "99", "600", "200.5", ""):
            with self.subTest(status=status):
                data = HEADER + (
                    f"2026-11-01 10:00:00,192.0.2.10,/,{status}\n"
                )

                result = self.run_analyzer(data)

                self.assert_rejected(
                    result,
                    "Every status must be a whole number from 100 to 599.",
                )


if __name__ == "__main__":
    unittest.main()