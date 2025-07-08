# How to Prepare the Details Sheet

## Finding Your Google Sheet ID

1. **Open your Google Sheet** that you're using for batch processing
2. **Look at the URL** - it will look like:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit
   ```
3. **Copy the ID** - it's the long string between `/d/` and `/edit`

Example:
- URL: `https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit`
- Sheet ID: `1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk`

## Running the Script

Once you have your Sheet ID, run:

```bash
python3 scripts/prepare_details_sheet.py YOUR_SHEET_ID_HERE
```

## What the Script Does

1. **Authenticates** using the service account at:
   - `config/credentials/theodore-service-account.json`

2. **Creates 'Details' sheet** if it doesn't exist

3. **Adds 71 column headers** (A through BS) for all CompanyData fields:
   - Core company information
   - Technology stack details
   - Business intelligence
   - Similarity metrics
   - Token usage and costs
   - And much more...

4. **Formats the headers** with:
   - Dark background, white text
   - Bold formatting
   - Frozen header row
   - Auto-sized columns

## Troubleshooting

If you get a 404 error:
1. Make sure you've shared the spreadsheet with the service account email
2. The service account email is in the JSON file at `config/credentials/theodore-service-account.json`
3. In Google Sheets: Share → Add the service account email → Editor permissions

If you get a permission error:
1. Check that the service account has "Editor" access, not just "Viewer"
2. Try re-sharing the sheet with the service account

## After Running

Once the Details sheet is prepared:
1. The batch processing will automatically populate data into this sheet
2. Each company will have its complete data across all 71 columns
3. The 'Companies' sheet will link to the Details sheet for each company