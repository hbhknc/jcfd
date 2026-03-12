# JCFD Fire Calls Dashboard (Streamlit)

## Files
- `app.py` — main Streamlit app
- `requirements.txt` — Python dependencies
- `JCFD Fire Calls - Dashboard v1.xlsx` — bundled sample data file

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud
1. Create a GitHub repo and upload these files.
2. In Streamlit Community Cloud, create a new app and point it to `app.py`.
3. Deploy.

## Notes
- You can replace the bundled Excel file with a newer export that has the same columns:
  - `Date`
  - `Address`
  - `Primary Call Type`
- The app also supports uploading `.xlsx`, `.xls`, or `.csv` files from the sidebar.
