# Theodore File Organization Reference

## Overview
This document describes the organized file structure of the Theodore AI Company Intelligence System after cleanup and reorganization.

## 📁 Directory Structure

```
Theodore/
├── 📄 Core Files
│   ├── app.py                          # Main Flask application
│   ├── v2_app.py                       # V2 Flask application
│   ├── requirements.txt                # Python dependencies
│   ├── .env                           # Environment variables
│   ├── .env.example                   # Environment template
│   ├── .gitignore                     # Git ignore rules
│   ├── CLAUDE.md                      # Main project documentation
│   └── README.md                      # Project overview
│
├── 📂 src/                            # Source code
│   ├── main_pipeline.py               # Core pipeline orchestration
│   ├── models.py                      # Pydantic data models
│   ├── intelligent_company_scraper.py # 4-phase scraping system
│   ├── bedrock_client.py              # AWS Bedrock AI integration
│   ├── gemini_client.py               # Google Gemini AI integration
│   ├── pinecone_client.py             # Vector database operations
│   ├── research_manager.py            # Structured research system
│   ├── similarity_engine.py           # Company similarity analysis
│   └── sheets_integration/            # Google Sheets integration
│       ├── google_sheets_service_client.py
│       ├── batch_processor_service.py
│       └── enhanced_batch_processor.py
│
├── 📂 scripts/                        # Organized scripts
│   ├── batch/                         # 🔥 BATCH PROCESSING SCRIPTS
│   │   ├── test_update_3_companies.py           # ⭐ Test integration (RECOMMENDED)
│   │   ├── process_user_sheet_companies.py     # ⭐ Production batch processing
│   │   ├── process_google_sheet_first_10.py    # Original batch processor
│   │   ├── batch_process_google_sheet.py       # Simple batch processor
│   │   ├── check_details_tab.py                # 🔍 Inspect Details tab
│   │   ├── check_sheet_tabs.py                 # 🔍 List all sheet tabs
│   │   ├── quick_check_sheet.py                # Quick sheet inspection
│   │   └── verify_spreadsheet_update.py        # Verify updates
│   │
│   ├── analysis/                      # Data analysis scripts
│   │   ├── analyze_before_after.py             # Before/after comparison
│   │   ├── analyze_database_sync.py            # Database sync analysis
│   │   ├── compare_data_improvements.py        # Data improvement comparison
│   │   ├── cost_analysis.py                    # Cost analysis
│   │   ├── data_improvement_summary.py         # Improvement summaries
│   │   ├── failure_analysis.py                 # Failure analysis
│   │   ├── final_enhancement_analysis.py       # Enhancement analysis
│   │   ├── quick_analysis.py                   # Quick data analysis
│   │   ├── quick_data_analysis.py              # Quick data insights
│   │   ├── specific_improvements_analysis.py   # Specific improvements
│   │   ├── reprocess_all_companies.py          # Reprocess all companies
│   │   ├── reprocess_companies_comprehensive.py # Comprehensive reprocessing
│   │   ├── reprocess_ten_companies.py          # Reprocess 10 companies
│   │   └── reprocessing_summary_report.py      # Reprocessing reports
│   │
│   ├── testing/                       # Debug and testing scripts
│   │   ├── debug_all_companies_crawling.py
│   │   ├── debug_connatix_leadership.py
│   │   ├── debug_extraction_content.py
│   │   ├── check_connatix_final_state.py
│   │   ├── check_updated_companies.py
│   │   └── quick_reprocess_test.py
│   │
│   ├── utilities/                     # Utility scripts
│   │   ├── export_to_csv.py                    # Export data to CSV
│   │   └── show_extracted_data.py              # Display extracted data
│   │
│   └── Core Scripts (existing)
│       ├── add_test_companies_with_similarity.py
│       ├── check_pinecone_database.py
│       ├── clear_pinecone.py
│       ├── extract_raw_pinecone_data.py
│       └── theodore_cli.py
│
├── 📂 tests/                          # Test files
│   ├── test_update_3_companies.py     # Google Sheets integration test
│   ├── test_real_company.py           # Single company test
│   ├── test_batch_reprocess_simple.py # Simple batch test
│   ├── test_enhanced_extraction.py    # Enhanced extraction test
│   ├── test_similarity_engine.py      # Similarity engine test
│   └── [40+ other test files...]
│
├── 📂 data/                           # Data storage
│   ├── exports/                       # 📊 Exported data files
│   │   ├── theodore_companies_enhanced_*.csv   # Company data exports
│   │   ├── enhanced_extraction_results_*.json # Extraction results
│   │   ├── theodore_cost_analysis.json        # Cost analysis data
│   │   └── [other CSV/JSON exports]
│   │
│   ├── logs/                          # 📝 Log files
│   │   ├── app.log                            # Application logs
│   │   └── [other log files]
│   │
│   ├── temp/                          # Temporary files
│   ├── company_details/               # Individual company JSON files
│   └── 2025 Survey Respondents Summary May 20.csv
│
├── 📂 config/                         # Configuration
│   ├── settings.py                    # Application settings
│   ├── sheets_field_mapping.py       # Google Sheets field mapping
│   └── credentials/                   # Authentication credentials
│       └── theodore-service-account.json
│
├── 📂 docs/                           # Documentation
│   ├── BATCH_RESEARCH.md             # 🔥 BATCH PROCESSING REFERENCE
│   ├── FILE_ORGANIZATION.md          # This file
│   ├── PROJECT_STRUCTURE.md          # Project structure
│   ├── DEVELOPER_ONBOARDING.md       # Developer guide
│   ├── FEATURE_SUMMARY.md            # Feature summary
│   └── [other documentation files...]
│
├── 📂 templates/                      # Web templates
│   ├── index.html                     # Main web interface
│   ├── v2_index.html                 # V2 web interface
│   └── settings.html                  # Settings page
│
├── 📂 static/                         # Static web assets
│   ├── css/style.css                  # Styles
│   ├── js/app.js                     # Main JavaScript
│   ├── js/v2_app.js                  # V2 JavaScript
│   └── img/favicon.ico               # Favicon
│
├── 📂 logs/                           # Processing logs
│   ├── processing_progress.json       # Progress tracking
│   ├── server.log                     # Server logs
│   └── intelligent_scraper_test_*.log # Scraper test logs
│
├── 📂 testing_sandbox/               # Development testing
│   ├── sheets_integration/            # Sheets integration tests
│   ├── minimal_test.py               # Minimal tests
│   ├── test_real_company.py          # Real company tests
│   └── [other sandbox files...]
│
└── 📂 archive/                       # Archived files
    ├── old_implementations/           # Old code versions
    ├── development_experiments/       # Development experiments
    ├── debug_scripts/                # Old debug scripts
    └── research/                     # Research files
```

## 🔥 Key Batch Processing Files

### Primary Scripts (scripts/batch/)
1. **test_update_3_companies.py** ⭐ - Test Google Sheets integration first
2. **process_user_sheet_companies.py** ⭐ - Production batch processing
3. **check_details_tab.py** 🔍 - Inspect current sheet content

### Commands After Reorganization
```bash
# Test integration (ALWAYS RUN FIRST)
python3 scripts/batch/test_update_3_companies.py

# Production batch processing
python3 scripts/batch/process_user_sheet_companies.py

# Check current sheet state
python3 scripts/batch/check_details_tab.py
```

## 📊 Data Organization

### exports/ - Generated Data
- **CSV exports**: Company data in spreadsheet format
- **JSON results**: Raw extraction results and analysis
- **Cost analysis**: Processing cost tracking

### logs/ - Processing Logs
- **Application logs**: Web app and API logs
- **Processing logs**: Batch processing progress
- **Debug logs**: Troubleshooting information

### company_details/ - Individual Company Data
- JSON files for each processed company
- Detailed extraction results
- Historical data versions

## 🛠️ Script Categories

### Batch Processing (scripts/batch/)
- Google Sheets integration
- Bulk company processing
- Sheet verification and debugging

### Analysis (scripts/analysis/)
- Data improvement analysis
- Before/after comparisons
- Cost analysis and reporting
- Reprocessing workflows

### Testing (scripts/testing/)
- Debug utilities
- Individual company testing
- Feature verification

### Utilities (scripts/utilities/)
- Data export tools
- Display utilities
- General purpose scripts

## 📝 Benefits of Organization

### Before Cleanup
- 50+ files scattered in root directory
- Difficult to find specific scripts
- No clear separation of concerns
- Batch processing scripts mixed with tests

### After Organization
- ✅ Clear categorical separation
- ✅ Easy to find batch processing scripts
- ✅ Logical grouping by function
- ✅ Clean root directory
- ✅ Documented file locations

## 🔍 Finding Files

### Need to process companies?
➡️ Look in `scripts/batch/`

### Need to analyze data?
➡️ Look in `scripts/analysis/`

### Need to test something?
➡️ Look in `tests/` or `scripts/testing/`

### Need exported data?
➡️ Look in `data/exports/`

### Need logs?
➡️ Look in `data/logs/` or `logs/`

## 🚨 Important Notes

### File Paths Updated
- All documentation has been updated with new paths
- BATCH_RESEARCH.md reflects new script locations
- Commands use `scripts/batch/` prefix

### Backward Compatibility
- Old import paths may need updating in some scripts
- All scripts maintained with proper `sys.path.insert(0, 'src')`
- Core functionality unchanged

### Maintenance
- Keep new files in appropriate directories
- Don't clutter root directory
- Use descriptive names for new scripts

This organization makes the Theodore project much more maintainable and user-friendly!