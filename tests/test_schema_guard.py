import importlib.util
import json
import io
import contextlib
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / ".claude" / "skills" / "_lib" / "ohs_data.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ohs_data_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SchemaGuardTests(unittest.TestCase):
    def test_schema_drift_reports_all_missing_columns(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp:
            workbook = Path(temp) / "schema-drift.xlsx"
            with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
                for key, sheet in module.SHEET_NAMES.items():
                    columns = list(module.REQUIRED_COLUMNS[key])
                    if key == "order":
                        columns.remove("LEGISLATION_CODE")
                        columns.remove("ORDER_TYPE")
                    pd.DataFrame(columns=columns).to_excel(writer, sheet_name=sheet, index=False)

            module.DATA_PATH = str(workbook)
            module._cache.clear()
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured), self.assertRaises(SystemExit) as raised:
                module.load_sheet("order")
            self.assertEqual(raised.exception.code, 1)
            payload = json.loads(captured.getvalue())
            self.assertEqual(payload["error"], "Source schema drift detected.")
            self.assertEqual(
                payload["missing_columns"],
                ["LEGISLATION_CODE", "ORDER_TYPE"],
            )
            module._cache["_xlfile"].close()
            module._cache.clear()

    def test_all_required_sheets_are_declared(self):
        module = load_module()
        self.assertEqual(set(module.REQUIRED_COLUMNS), set(module.SHEET_NAMES))


if __name__ == "__main__":
    unittest.main()
