import csv
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ANALYZER = Path(__file__).resolve().with_name("analyzer.py")
HEADER = "timestamp,ip,path,status\n"


class HourlyTests(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.work_dir = Path(temp_dir.name)

    def run_analyzer(self, rows):
        input_file = self.work_dir / "logs.csv"
        input_file.write_text(HEADER + rows, encoding="utf-8")

        return subprocess.run(
            [sys.executable, str(ANALYZER), str(input_file)],
            cwd=self.work_dir,
            env={**os.environ, "MPLBACKEND": "Agg"},
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_hourly_report(self):
        # Unsorted input includes the same hour on two different days.
        result = self.run_analyzer(
            "2026-11-02 10:15:00,192.0.2.10,/,200\n"
            "2026-11-01 11:00:00,192.0.2.11,/api,500\n"
            "2026-11-01 10:59:59,192.0.2.10,/missing,404\n"
            "2026-11-01 10:00:00,192.0.2.10,/,200\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        report = self.work_dir / "reports" / "hourly_report.csv"
        with report.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))

        actual = [
            (
                row["hour"],
                int(row["requests"]),
                int(row["client_errors"]),
                int(row["server_errors"]),
                int(row["total_errors"]),
                float(row["error_rate_percent"]),
            )
            for row in rows
        ]

        self.assertEqual(
            actual,
            [
                ("2026-11-01 10:00:00", 2, 1, 0, 1, 50.0),
                ("2026-11-01 11:00:00", 1, 0, 1, 1, 100.0),
                ("2026-11-02 10:00:00", 1, 0, 0, 0, 0.0),
            ],
        )

    def test_invalid_timestamps(self):
        for timestamp in (
            "",
            "not-a-date",
            "2026-02-30 10:00:00",
            "2026-11-01 25:00:00",
            "2026-11-01",
            "2026-1-01 10:00:00",
        ):
            with self.subTest(timestamp=timestamp):
                result = self.run_analyzer(
                    "2026-11-01 09:00:00,192.0.2.10,/,200\n"
                    f"{timestamp},192.0.2.11,/login,200\n"
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Invalid timestamp in data row 2.", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse((self.work_dir / "reports").exists())


if __name__ == "__main__":
    unittest.main()