# Google Sheets Integration Test Structure

This directory contains test scripts and tools for the Google Sheets integration.

## Directory Structure

```
testing_sandbox/sheets_integration/
├── cli_tools/              # Command-line test scripts
│   ├── test_auth.py        # OAuth authentication test
│   ├── test_auth_simple.py # Simple auth test
│   ├── test_batch_processing.py  # OAuth batch processing test
│   ├── test_batch_service.py     # Service account batch test
│   ├── test_service_auth.py      # Service account auth test
│   ├── test_sheet_creation.py    # Sheet creation test
│   └── test_single_company.py    # Single company test
├── credentials/            # Place credentials here (gitignored)
├── test_sheets/           # Sample data for testing
├── api_tests/             # API testing examples
├── mock_data/             # Mock data for testing
└── integration_tests/     # Integration test scripts
```

## Main Implementation Files

The main implementation files have been moved to:
- `src/sheets_integration/google_sheets_service_client.py` - Service account client
- `src/sheets_integration/batch_processor_service.py` - Batch processing service

## Documentation

Documentation has been moved to:
- `docs/sheets_integration/SERVICE_ACCOUNT_SETUP.md` - How to set up service account
- `docs/sheets_integration/IMPLEMENTATION_SUMMARY.md` - Implementation overview
- `docs/sheets_integration/TESTING_GUIDE.md` - Testing guide

## Legacy Files

The following files remain for backward compatibility but should be considered deprecated:
- `google_sheets_client.py` - OAuth-based client (legacy)
- `batch_processor.py` - OAuth-based batch processor (legacy)
- `service_account_auth.py` - Standalone auth test (legacy)

## Testing Quick Start

1. Ensure you have service account credentials at `theodore-service-account.json`
2. Run a simple test: `python cli_tools/test_service_auth.py`
3. Test single company: `python cli_tools/test_single_company.py`
4. Test batch processing: `python cli_tools/test_batch_service.py`