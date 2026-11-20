import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from component_price_scraper import PriceMonitor, ScraperConfig


class PriceMonitorIntegrationTests(unittest.TestCase):
    def test_excel_output_and_price_history(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "input.xlsx"
            output = root / "output.xlsx"
            history = root / "history.xlsx"
            pd.DataFrame({
                "Supplier": [1000, None, 2500],
                "Quantity": [2, 1, 3],
                "Comment": ["first", "empty", "third"],
            }).to_excel(source, index=False)

            config = ScraperConfig(
                input_file=source,
                output_file=output,
                history_file=history,
                auto_open=False,
                show_progress=False,
            )
            first = PriceMonitor(config).run()
            self.assertEqual(first.successful, 2)
            self.assertEqual(first.not_found, 1)
            self.assertEqual(first.grand_total, 9500)

            history_rows = list(load_workbook(history, data_only=True).active.values)
            self.assertEqual(history_rows[0][0], "Date / Time")
            self.assertEqual(history_rows[1][1], 9500)

            second = PriceMonitor(config).run()
            self.assertEqual(second.grand_total, 9500)
            history_rows = list(load_workbook(history, data_only=True).active.values)
            self.assertEqual(len(history_rows), 3)
            self.assertEqual(history_rows[2][1], 9500)
            self.assertEqual(history_rows[2][2], 0)

            report = load_workbook(output, data_only=True).active
            self.assertEqual(report.cell(1, 4).value, "Status")
            self.assertEqual(report.cell(5, 5).value, "Grand Total")
            self.assertEqual(report.cell(5, 6).value, 9500)


if __name__ == "__main__":
    unittest.main()
