# Data directory

The source workbook is intentionally excluded from Git.

Download the current Employer Records XLSX from the government catalogue:

```powershell
python scripts/refresh_data.py
```

The script writes the selected resource atomically to:

```text
data/2024_ohs-employer-record-open-data.xlsx
```

The stable local filename preserves compatibility with the analytical skills even if the catalogue resource name changes. A refresh receipt is written to `data/refresh-receipt.json`.

Source catalogue: https://open.canada.ca/data/en/dataset/a2772d8c-48be-4d39-bcf2-dafca456d724

Data licence: https://open.alberta.ca/licence
