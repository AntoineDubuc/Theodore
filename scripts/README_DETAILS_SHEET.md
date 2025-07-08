# Prepare Details Sheet Script

This script prepares the Google Sheets 'Details' tab with proper headers for all CompanyData fields.

## Purpose

The batch processing system writes company data to two sheets:
1. **Companies** sheet - Progress tracking with summary data
2. **Details** sheet - Complete data with all 71+ fields from CompanyData model

This script ensures the Details sheet has the correct headers matching our field mapping.

## Usage

```bash
python scripts/prepare_details_sheet.py <spreadsheet_id>
```

Example:
```bash
python scripts/prepare_details_sheet.py 1UEzGinv3IkR35F1UU6JdhiizNoLfaR1E0Vf4QXafbCw
```

## What It Does

1. **Creates Details sheet if missing** - Adds a new 'Details' tab if it doesn't exist
2. **Adds all field headers** - 71 columns from A to BS representing all CompanyData fields
3. **Formats headers** - Dark background, white text, bold formatting
4. **Freezes rows/columns** - Freezes header row and first two columns (ID, Company Name)
5. **Auto-resizes columns** - Adjusts column widths for better readability

## Field Categories

The Details sheet includes all fields organized into these categories:

- **Core Identity (A-F)**: ID, name, website, industry, business model, size
- **Technology Stack (G-I)**: Tech stack, chat widget, forms
- **Business Intelligence (J-P)**: Pain points, services, advantages, description
- **Company Details (Q-AC)**: Location, employees, culture, funding, social, contacts
- **Similarity Metrics (AD-AM)**: Stage, tech level, geographic scope, confidence scores
- **Batch Research Intelligence (AN-AU)**: Job listings, products, decision makers
- **AI Analysis (AV-AX)**: Raw content, AI summary, embeddings
- **System Metadata (AY-BB)**: Created/updated dates, status, errors
- **SaaS Classification (BC-BH)**: Classification, confidence, justification
- **Additional Fields (BI-BP)**: Framework, scraped data, LLM details
- **Token & Cost Tracking (BQ-BS)**: Input/output tokens, total cost

## Prerequisites

1. Service account JSON file at: `~/theodore-service-account.json`
2. Service account must have edit access to the spreadsheet
3. Python packages: `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`

## Notes

- The script is idempotent - safe to run multiple times
- It preserves existing data in the Details sheet
- Only updates the header row (row 1)
- Compatible with the Antoine batch processing system