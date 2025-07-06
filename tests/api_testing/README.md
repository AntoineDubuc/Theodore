# Theodore API Testing Suite

This directory contains comprehensive API testing tools for the Theodore system.

## 📋 Files Overview

### Testing Scripts
- **`comprehensive_endpoint_test.py`** - Main testing script that validates all Theodore API endpoints
- **`API_ENDPOINT_DOCUMENTATION.md`** - Comprehensive API documentation with correct usage examples

### Usage

```bash
# Run from Theodore root directory
python3 tests/api_testing/comprehensive_endpoint_test.py
```

### API Documentation
For correct API usage, see `API_ENDPOINT_DOCUMENTATION.md` which includes:
- Correct parameter names and structures for each endpoint
- Working curl command examples
- Common issues and fixes

### Prerequisites
- Theodore application must be running on `http://localhost:5002`
- Python 3.x with requests library installed

### Test Coverage
- **System Health** - Core system status and diagnostics
- **Research** - Company research and analysis endpoints
- **Discovery** - Similarity search and discovery
- **Database** - Company data management
- **Progress** - Real-time progress tracking
- **Classification** - Business model classification
- **Settings** - Configuration management
- **Field Metrics** - Data quality metrics

### Output
- Real-time progress logging in terminal
- Comprehensive markdown reports generated in `tests/reports/`
- Success/failure summary with performance metrics

### Reports Generated
Reports are saved to `tests/reports/` directory:
- `theodore_api_test_report_YYYYMMDD_HHMMSS.md` - Full detailed report
- `comprehensive_api_test_summary.md` - Executive summary

### Test Features
- **Performance Monitoring** - Response time measurement
- **Error Classification** - Different failure types (failed, timeout, error)
- **Human-Readable Summaries** - Clear interpretation of API responses
- **Comprehensive Coverage** - Tests all available endpoints
- **Detailed Logging** - Real-time progress during execution