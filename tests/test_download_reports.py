import json
import shutil
import tempfile
import unittest
from pathlib import Path

from collectors.download_reports import CompanyReportAgent


class DownloadReportsTests(unittest.TestCase):
    def test_analyze_handles_single_row_downloaded_tables(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(__file__).resolve().parents[1]
            reports_dir = repo_root / 'reports'
            symbol_dir = reports_dir / 'TEST_STOCK'

            try:
                if symbol_dir.exists():
                    shutil.rmtree(symbol_dir)

                symbol_dir.mkdir(parents=True, exist_ok=True)
                (symbol_dir / 'table_0.csv').write_text(
                    'Metric,Value\nCompounded Sales Growth,12%\n',
                    encoding='utf-8'
                )
                (symbol_dir / 'table_1.csv').write_text(
                    'Metric,Value\nCompounded Profit Growth,14%\n',
                    encoding='utf-8'
                )
                (symbol_dir / 'table_2.csv').write_text(
                    'Metric,Latest\nOPM,26%\n',
                    encoding='utf-8'
                )
                (symbol_dir / 'metadata.json').write_text(json.dumps({
                    'tables': {
                        'table_0': {'column_names': ['Compounded Sales Growth'], 'preview': 'Compounded Sales Growth'},
                        'table_1': {'column_names': ['Compounded Profit Growth'], 'preview': 'Compounded Profit Growth'},
                        'table_2': {'column_names': ['Operating Profit'], 'preview': 'Operating Profit Margin'},
                    }
                }), encoding='utf-8')

                result = CompanyReportAgent().analyze('TEST_STOCK')

                self.assertGreaterEqual(result['report_score'], 0)
                self.assertIsInstance(result['reasons'], list)
            finally:
                if symbol_dir.exists():
                    shutil.rmtree(symbol_dir)


if __name__ == '__main__':
    unittest.main()
