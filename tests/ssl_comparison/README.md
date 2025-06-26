# SSL Comparative Testing for Theodore

## Overview

This directory contains a comparative testing framework to scientifically measure the impact of SSL certificate fixes on Theodore's company intelligence scraping system.

## Test Methodology

### Purpose
Demonstrate that SSL certificate issues are preventing Theodore from successfully crawling websites and extracting company intelligence, and prove that SSL fixes resolve these issues.

### Approach
- **Control Test**: Test current Theodore system (with SSL issues)
- **Treatment Test**: Test with SSL fixes applied in isolation
- **Comparative Analysis**: Generate quantitative before/after metrics

### Key Metrics Measured
1. **Link Discovery Success**: Number of URLs discovered vs 0 URLs
2. **Page Selection Method**: LLM-driven vs heuristic fallback usage
3. **Content Extraction Success**: Successful page extractions vs failures
4. **Overall Processing Success**: Completed companies vs failed companies
5. **Data Quality**: Populated fields vs empty/missing fields

## Directory Structure

```
ssl_comparison/
├── README.md                    # This file - test overview
├── control_test/               # Baseline testing (current system)
│   ├── test_ssl_control.py    # Control test script
│   ├── control_results/       # JSON results from control test
│   └── control_logs/          # Detailed logs from control test
├── treatment_test/             # SSL-fixed testing
│   ├── test_ssl_treatment.py  # Treatment test script  
│   ├── ssl_config.py          # Isolated SSL configuration
│   ├── treatment_results/     # JSON results from treatment test
│   └── treatment_logs/        # Detailed logs from treatment test
├── analysis/                   # Comparison and reporting
│   ├── generate_comparison_report.py  # Main analysis script
│   ├── comparison_results/    # Final comparison data
│   └── charts/                # Visual comparison charts (optional)
├── test_data/                  # Shared test resources
│   ├── company_list.json      # Standardized test companies
│   └── expected_metrics.json  # Expected baseline metrics
└── reports/                    # Final outputs
    ├── SSL_COMPARISON_REPORT.md       # Final markdown report
    ├── control_summary.json          # Control test summary
    ├── treatment_summary.json        # Treatment test summary
    └── improvement_metrics.json      # Calculated improvements
```

## How to Run the Tests

### Prerequisites
1. Theodore system must be running (`python app.py`)
2. Virtual environment activated with Theodore dependencies
3. API keys configured in `.env` file
4. Internet access to fetch companies from Google Sheets

### Step 0: Generate Test Company Data
```bash
cd tests/ssl_comparison/test_data
python fetch_companies.py 8
```

This will:
- Fetch 8 random companies from the 6000+ company Google Sheets dataset
- Validate that companies have both names and websites
- Generate `company_list.json` for both control and treatment tests

### Step 1: Run Control Test (Baseline)
```bash
cd tests/ssl_comparison/control_test
python test_ssl_control.py
```

This will:
- Test the fetched companies using current Theodore system
- Document SSL failures and link discovery issues
- Generate baseline metrics in `control_results/`

### Step 2: Run Treatment Test (With SSL Fix)
```bash
cd tests/ssl_comparison/treatment_test  
python test_ssl_treatment.py
```

This will:
- Test the same companies with SSL fixes applied
- Document improved link discovery and page selection
- Generate enhanced metrics in `treatment_results/`

### Step 3: Generate Comparison Report
```bash
cd tests/ssl_comparison/analysis
python generate_comparison_report.py
```

This will:
- Load both control and treatment results
- Calculate improvement percentages
- Generate final comparison report in `reports/`

## Expected Results

### Before SSL Fix (Control)
- **Link Discovery**: 0 URLs discovered for most companies
- **Page Selection**: Falls back to heuristic selection due to no links
- **Content Extraction**: Minimal content extracted
- **Processing Success**: High failure rate due to SSL errors

### After SSL Fix (Treatment)  
- **Link Discovery**: 10-50+ URLs discovered per company
- **Page Selection**: LLM-driven intelligent page selection works
- **Content Extraction**: Comprehensive content from multiple pages
- **Processing Success**: High success rate with proper SSL handling

## Test Companies

The test uses real companies randomly selected from a 6000+ company Google Sheets dataset:

- **Data Source**: https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit?gid=0#gid=0
- **Selection Method**: Random sampling of companies with valid names and websites
- **Sample Size**: Configurable (default: 8 companies)
- **Validation**: Ensures companies have both company names and website URLs
- **Diversity**: Real-world dataset covering multiple industries and company sizes

## Safety & Isolation

- ✅ **No Theodore Code Changes**: All SSL fixes applied in isolated test scope
- ✅ **Non-Destructive**: Tests only read from Theodore's API endpoints  
- ✅ **Reproducible**: Can be run multiple times safely
- ✅ **Reversible**: No permanent changes to Theodore system

## Interpreting Results

### Success Indicators
- **Link Discovery**: >80% of companies return >0 URLs in treatment vs control
- **Page Selection**: LLM success rate >50% in treatment vs 0% in control
- **Content Quality**: Significantly more populated fields in treatment
- **Processing Speed**: Faster processing due to fewer timeouts and retries

### Report Outputs
- **`SSL_COMPARISON_REPORT.md`**: Human-readable summary with recommendations
- **`improvement_metrics.json`**: Quantitative improvement data
- **Timestamped result files**: Detailed per-company comparison data

## Next Steps

If tests demonstrate clear SSL fix benefits:
1. Review implementation recommendations in the final report
2. Apply SSL fixes to Theodore's production codebase
3. Re-run model comparison testing to verify functionality
4. Document SSL configuration in Theodore's setup guide

---

**Generated**: 2025-06-26  
**Purpose**: Quantify SSL certificate fix impact on Theodore's company intelligence extraction  
**Status**: Ready for execution