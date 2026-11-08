import csv
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT_DIR = Path(__file__).resolve().parent
ANALYZER = PROJECT_DIR / "analyzer.py"
SAMPLE = PROJECT_DIR / "sample_nginx.log"


class NginxTests(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.work_dir = Path(temp_dir.name)

    def run_analyzer(self, log_file):
        return subprocess.run(
            [sys.executable, str(ANALYZER), str(log_file)],
            cwd=self.work_dir,
            capture_output=True,
            text=True,
            env={**os.environ, "MPLBACKEND": "Agg"},
            timeout=60,
        )

    def test_nginx_sample_groups_requests_by_utc_hour(self):
        result = self.run_analyzer(SAMPLE)
        self.assertEqual(result.returncode, 0, result.stderr)

        reports = self.work_dir / "reports"
        summary = (reports / "summary.txt").read_text(encoding="utf-8")
        self.assertIn("Total requests: 3", summary)
        self.assertIn("Error rate: 66.7%", summary)

        with (reports / "hourly_report.csv").open(
            encoding="utf-8", newline=""
        ) as file:
            hours = [
                (
                    row["hour"],
                    int(row["requests"]),
                    int(row["client_errors"]),
                    int(row["server_errors"]),
                )
                for row in csv.DictReader(file)
            ]

        self.assertEqual(
            hours,
            [
                ("2026-10-31 09:00:00", 1, 0, 0),
                ("2026-10-31 10:00:00", 2, 1, 1),
            ],
        )

        with (reports / "errors.csv").open(
            encoding="utf-8", newline=""
        ) as file:
            errors = [
                (row["path"], row["status"])
                for row in csv.DictReader(file)
            ]

        self.assertCountEqual(
            errors,
            [("/missing", "404"), ("/api/orders", "500")],
        )

    def test_broken_nginx_line_reports_its_line_number(self):
        log_file = self.work_dir / "broken.log"
        log_file.write_text(
            '192.0.2.20 - - [31/Oct/2026:10:00:00 +0000] '
            '"GET / HTTP/1.1" 200 512 "-" "sample-client"\n'
            'this is a broken log line\n',
            encoding="utf-8",
        )

        result = self.run_analyzer(log_file)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Line 2:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((self.work_dir / "reports").exists())


if __name__ == "__main__":
    unittest.main()