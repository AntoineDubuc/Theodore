# Google Sheets Integration Documentation

This directory contains documentation for Theodore's Google Sheets integration feature.

## Overview

The Google Sheets integration allows users to batch process companies through Google Sheets using a service account for authentication. This provides a familiar spreadsheet interface for managing large-scale company research operations.

## Documentation Files

### Setup & Configuration
- **[SERVICE_ACCOUNT_SETUP.md](SERVICE_ACCOUNT_SETUP.md)** - Step-by-step guide for setting up Google service account authentication
- **[google_sheets_batch_processing_plan.md](google_sheets_batch_processing_plan.md)** - Original architecture and planning document

### Implementation
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical implementation details and architecture overview
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing guide for all integration features

## Quick Start

1. **Set up Service Account**: Follow [SERVICE_ACCOUNT_SETUP.md](SERVICE_ACCOUNT_SETUP.md)
2. **Configure Environment**: Add service account JSON to project
3. **Test Authentication**: Run `python testing_sandbox/sheets_integration/cli_tools/test_service_auth.py`
4. **Process Companies**: Use batch processor for multi-company research

## Architecture Summary

```
Google Sheets → Service Account Auth → Theodore API → AI Research → Results in Sheet
```

### Key Components

- **GoogleSheetsServiceClient** (`src/sheets_integration/google_sheets_service_client.py`)
  - Handles all Google Sheets API operations
  - Service account authentication
  - Sheet reading/writing operations

- **BatchProcessorService** (`src/sheets_integration/batch_processor_service.py`)
  - Manages concurrent company processing
  - Progress tracking and error handling
  - Real-time sheet updates

## Features

- ✅ Service account authentication (no browser prompts)
- ✅ Batch processing with concurrency control
- ✅ Real-time progress updates in sheets
- ✅ Error handling and retry logic
- ✅ Structured data output with all research fields
- ✅ Integration with main Theodore pipeline

## Testing

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for detailed testing instructions.

Test scripts are located in `testing_sandbox/sheets_integration/cli_tools/`