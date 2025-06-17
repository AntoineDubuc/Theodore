# Google Sheets Integration Testing Sandbox

This isolated testing environment is for developing and testing Google Sheets batch processing integration for Theodore.

## Setup Instructions

1. **OAuth2 Credentials**: The credentials file is located at:
   ```
   /Users/antoinedubuc/Desktop/AI_Goodies/Theodore/client_secret_1096944990043-5u1eohnobc583lvueqr2cvfvm9tcjc3p.apps.googleusercontent.com.json
   ```

2. **Test Google Sheet**: 
   - URL: https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit?usp=sharing
   - Shared with: theodore.salesbot@gmail.com
   - Contains two tabs: 'Companies' (with 6000 rows) and 'Details' (for complete research data)

3. **Required Packages** (already installed):
   - google-auth
   - google-auth-oauthlib
   - google-auth-httplib2
   - google-api-python-client

## Directory Structure

```
sheets_integration/
├── README.md                    # This file
├── cli_tools/                   # Standalone testing tools
│   ├── test_auth.py            # Test Google Sheets authentication
│   ├── test_sheet_creation.py  # Test dual-sheet creation
│   └── test_batch_processing.py # Test company processing
├── api_tests/                   # API endpoint tests
├── mock_data/                   # Test data and mocks
├── integration_tests/           # End-to-end tests
├── credentials/                 # Credentials storage
└── test_sheets/                # Test sheet templates
```

## Testing Workflow

1. Test authentication: `python cli_tools/test_auth.py`
2. Test sheet operations: `python cli_tools/test_sheet_creation.py`
3. Test batch processing: `python cli_tools/test_batch_processing.py`
4. Run test server: `python test_server.py`

## Important Notes

- OAuth2 redirect URIs configured in Google Cloud Console:
  - http://localhost:5002/auth/google/callback
  - http://localhost:5555/auth/google/callback
- Test server runs on port 5555 to avoid conflicts with main app (5002)
- Uses real Google Sheets API, no mocking