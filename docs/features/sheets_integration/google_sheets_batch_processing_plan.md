# Google Sheets Batch Processing Integration Plan

## 📋 Project Overview

**Objective**: Integrate Google Sheets as a batch processing source for Theodore's company research pipeline, allowing users to process multiple companies efficiently through a familiar spreadsheet interface.

**Approach**: Simplified Gmail-based sharing model where users share their Google Sheet with a dedicated Theodore Gmail account.

## 🎯 Core Design Principles

1. **User-Friendly**: Simple as sharing any Google Doc
2. **Familiar Interface**: Users work in Google Sheets they already know
3. **Real-Time Updates**: Live progress tracking in the sheet
4. **Minimal Setup**: No complex authentication or API setup required
5. **Secure**: Standard Google permissions model

## 🏗️ Technical Architecture

### Authentication Model
- **Theodore Gmail Account**: `theodore.ai.research@gmail.com` (or similar)
- **Access Method**: OAuth2 with stored refresh token
- **Permission Level**: Editor access to shared sheets only
- **Security**: Standard Google sharing permissions

### Data Flow
```
User Sheet → Share with Theodore Gmail → Theodore Web UI → Batch Processor → AI Research → Sheet Updates → Pinecone Storage
```

## 📊 Google Sheet Structure

### Required User Columns (Minimum)
| Column | Name | Purpose | Required | Example |
|--------|------|---------|----------|---------|
| A | `company_name` | Company to research | ✅ | "Anthropic" |
| B | `website` | Known website (optional) | ❌ | "anthropic.com" |

### Auto-Generated Theodore Columns (Main Sheet)
| Column | Name | Purpose | Type | Example |
|--------|------|---------|------|---------|
| C | `status` | Processing status | Auto | `pending/processing/completed/failed` |
| D | `progress` | Completion percentage | Auto | `75%` |
| E | `research_date` | When processed | Auto | `2025-06-13 14:30:22` |
| F | `industry` | Discovered industry | Auto | `Artificial Intelligence` |
| G | `company_stage` | Company stage | Auto | `Enterprise` |
| H | `tech_sophistication` | Tech level | Auto | `High` |
| I | `ai_summary` | Research summary | Auto | `AI safety company focused on...` |
| J | `full_data_sheet` | Link to complete data | Auto | `=HYPERLINK("Sheet2!A5", "View Details")` |
| K | `pinecone_id` | Storage reference | Auto | `dd2c18dc-b692-...` |
| L | `error_notes` | Failure details | Auto | `Website unreachable` |

### Complete Data Export (Secondary Sheet)
**Problem**: CompanyData model has 62+ fields - too many for a single readable sheet
**Solution**: Hierarchical dual-sheet approach (Option 1)

**Sheet 2 - "Complete Research Data"**: 
- **Structure**: All CompanyData fields as columns (A-BL+)
- **Content**: Each row = one company's complete research data
- **Access**: Hyperlinked from main sheet's "View Details" column
- **Purpose**: Full data export for detailed analysis and processing

**Complete Field Mapping (62+ fields from models.py)**:
```
Core Identity (A-F):
├── id, name, website, industry, business_model, company_size

Technology Stack (G-I): 
├── tech_stack, has_chat_widget, has_forms

Business Intelligence (J-P):
├── pain_points, key_services, competitive_advantages, target_market,
├── company_description, value_proposition, founding_year

Company Details (Q-Z):
├── location, employee_count_range, company_culture, funding_status,
├── social_media, contact_info, leadership_team, recent_news,
├── certifications, partnerships, awards

Crawling Metadata (AA-AC):
├── pages_crawled, crawl_depth, crawl_duration

Similarity Metrics (AD-AL):
├── company_stage, tech_sophistication, geographic_scope,
├── business_model_type, decision_maker_type, sales_complexity,
├── stage_confidence, tech_confidence, industry_confidence

Batch Research Intelligence (AM-AS):
├── has_job_listings, job_listings_count, job_listings_details,
├── products_services_offered, key_decision_makers, funding_stage_detailed,
├── sales_marketing_tools, recent_news_events

AI Analysis (AT-AV):
├── raw_content, ai_summary, embedding

System Metadata (AW-AZ):
├── created_at, last_updated, scrape_status, scrape_error
```

**Navigation Flow**:
1. User works in "Sheet 1" for progress tracking
2. Clicks "View Details" link to jump to specific row in "Sheet 2"  
3. Can analyze complete data or export for further processing

### Optional Input Columns (Future Enhancement)
- `priority` - Processing priority (1-5)
- `industry_hint` - Known industry context
- `size_hint` - Known company size
- `notes` - Additional research context

## 🔄 User Workflow

### Step 1: Sheet Preparation
1. User creates Google Sheet with company list
2. Adds required columns: `company_name`, optionally `website`
3. Shares sheet with `theodore.ai.research@gmail.com` (Editor access)

### Step 2: Batch Processing
1. User opens Theodore web interface
2. Pastes Google Sheet URL into batch processing section
3. Clicks "Start Batch Processing"
4. Theodore validates access and sheet structure

### Step 3: Real-Time Processing
1. Theodore processes companies in parallel (3-5 at once)
2. Updates sheet with real-time progress
3. Stores complete research data in Pinecone
4. Handles errors gracefully with detailed notes

### Step 4: Results Review
1. User sees completed research in their sheet
2. Can access full company details through Theodore web interface
3. Data is available for similarity analysis and discovery

## 🛠️ Implementation Components

### New Files to Create
```
src/google_sheets_client.py        # Google Sheets API wrapper with dual-sheet support
src/batch_processor.py             # Queue management and parallel processing
src/google_sheets_auth.py          # OAuth2 authentication for Theodore Gmail
scripts/batch_process_sheet.py     # CLI entry point for batch processing
config/google_sheets_config.py     # Configuration settings
config/sheets_field_mapping.py     # Complete field mapping (62+ fields) ✅ CREATED
```

### Web Interface Additions
```html
<!-- Add to existing Theodore interface -->
<div class="batch-processing-section">
    <h3>📊 Batch Process Google Sheet</h3>
    <div class="instructions">
        <p>1. Share your Google Sheet with: <code>theodore.ai.research@gmail.com</code></p>
        <p>2. Paste your sheet URL below and start processing</p>
    </div>
    
    <input type="url" id="sheetUrl" placeholder="https://docs.google.com/spreadsheets/d/..." />
    <button onclick="startBatchProcessing()">Start Batch Processing</button>
    
    <div class="batch-progress" style="display: none;">
        <div class="progress-bar"></div>
        <div class="status-text">Processing companies...</div>
        <div class="company-status">
            <span class="completed">5 completed</span>
            <span class="processing">2 processing</span>
            <span class="pending">8 pending</span>
        </div>
    </div>
</div>
```

### API Endpoints to Add
```
POST /api/batch/start           # Start batch processing
GET  /api/batch/status/<job_id> # Get batch progress
GET  /api/batch/jobs            # List active batch jobs
POST /api/batch/stop/<job_id>   # Stop batch processing
```

## ⚙️ Configuration Requirements

### Environment Variables
```bash
# Google Sheets Integration
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/oauth_credentials.json
GOOGLE_SHEETS_REFRESH_TOKEN=stored_refresh_token
THEODORE_GMAIL_ACCOUNT=theodore.ai.research@gmail.com

# Batch Processing Settings
BATCH_PROCESSING_CONCURRENCY=5         # Companies processed simultaneously
BATCH_PROGRESS_UPDATE_INTERVAL=30      # Sheet update frequency (seconds)
BATCH_MAX_COMPANIES_PER_SHEET=100      # Safety limit
BATCH_REQUEST_TIMEOUT=60               # Per-company timeout (seconds)
```

### Google Sheets Configuration
```python
# config/google_sheets_config.py
THEODORE_GMAIL = "theodore.ai.research@gmail.com"
SHEETS_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Column mapping for sheet structure
REQUIRED_COLUMNS = {
    'company_name': 'A',
    'website': 'B'  # Optional
}

AUTO_GENERATED_COLUMNS = {
    'status': 'C',
    'progress': 'D', 
    'research_date': 'E',
    'industry': 'F',
    'company_stage': 'G',
    'tech_sophistication': 'H',
    'pinecone_id': 'I',
    'error_notes': 'J'
}

BATCH_SETTINGS = {
    'concurrency': 5,
    'update_interval': 30,
    'max_retries': 3,
    'timeout_per_company': 60
}
```

## 🔄 Processing Workflow (Option 1: Dual-Sheet Approach)

### Phase 1: Sheet Setup & Validation
1. Extract sheet ID from user-provided URL
2. Verify Theodore has Editor access to the workbook
3. **Create/Validate dual-sheet structure**:
   - "Progress Tracking" sheet (main user interface)
   - "Complete Research Data" sheet (full field export)
4. Validate required columns in Progress Tracking sheet
5. Count companies and check safety limits
6. Identify pending/failed companies to process

### Phase 2: Sheet Preparation
1. **Setup Progress Tracking sheet** with headers (A-L columns)
2. **Setup Complete Data sheet** with all 62+ field headers (A-BB columns)
3. **Create hyperlinks** from Progress sheet to Complete Data sheet
4. **Apply formatting**: Headers, status colors, frozen rows/columns
5. Initialize progress tracking for batch job

### Phase 3: Parallel Processing with Dual Updates
```python
async def process_batch_with_dual_sheets(companies, progress_sheet, complete_sheet):
    semaphore = asyncio.Semaphore(BATCH_CONCURRENCY)
    
    async def process_company(company, row_number):
        async with semaphore:
            # Update progress sheet status
            update_progress_sheet_status(progress_sheet, row_number, 'processing')
            
            try:
                # Full company research
                result = await theodore_pipeline.research_company(company.name)
                
                # Update both sheets simultaneously
                progress_row = company_data_to_progress_row(result, row_number)
                complete_row = company_data_to_complete_row(result)
                
                update_progress_sheet_row(progress_sheet, row_number, progress_row)
                update_complete_data_row(complete_sheet, row_number, complete_row)
                
                # Store in Pinecone
                pinecone_client.upsert_company(result)
                
            except Exception as e:
                update_progress_sheet_status(progress_sheet, row_number, 'failed', str(e))
    
    await asyncio.gather(*[process_company(c, i) for i, c in enumerate(companies, 2)])
```

### Phase 4: Results & Navigation Setup
1. **Update final statistics** in both sheets
2. **Activate hyperlinks** for navigation between sheets
3. **Format completion status** with color coding
4. **Generate summary report** in progress sheet header
5. Clean up temporary processing data
6. Send completion notification (if configured)

## 🛡️ Security & Error Handling

### Security Measures
- **Minimum Permissions**: Only Editor access to shared sheets
- **Data Privacy**: Only read/write specified columns
- **Access Validation**: Verify permissions before processing
- **Rate Limiting**: Respect Google Sheets API quotas

### Error Handling Strategy
```python
ERROR_CATEGORIES = {
    'PERMISSION_DENIED': 'Sheet not shared with Theodore or insufficient permissions',
    'INVALID_STRUCTURE': 'Required columns missing or incorrectly formatted',
    'RESEARCH_FAILED': 'Company research failed (network, AI, or data issues)',
    'RATE_LIMITED': 'Google Sheets API rate limit exceeded',
    'TIMEOUT': 'Company research exceeded timeout limit'
}

# Retry strategy
RETRY_CONFIG = {
    'max_attempts': 3,
    'backoff_multiplier': 2,
    'retriable_errors': ['RATE_LIMITED', 'TIMEOUT', 'NETWORK_ERROR']
}
```

### Graceful Degradation
- Continue processing valid companies if some fail
- Provide detailed error messages for failures
- Allow resuming processing from failures
- Maintain processing state across interruptions

## 📈 Implementation Phases

### Phase 0: Isolated Testing Sandbox (1-2 hours) 🔬
**Priority**: HIGHEST - Complete isolation from main application
**Purpose**: Validate Google Sheets integration without touching production UI

**Components**:
- [ ] Create isolated testing directory: `testing_sandbox/sheets_integration/`
- [ ] Set up minimal Google Sheets API authentication
- [ ] Create test Google Sheet templates
- [ ] Build standalone CLI tools for testing
- [ ] Implement core API endpoints for sheet operations

**Deliverables**:
- Isolated testing environment 
- CLI tools for manual testing
- API endpoints that can be tested with curl/Postman
- Clear credential setup documentation

**Testing Approach**:
```bash
# Isolated testing commands
python testing_sandbox/sheets_integration/test_auth.py
python testing_sandbox/sheets_integration/test_sheet_creation.py
python testing_sandbox/sheets_integration/test_batch_processing.py

# API endpoint testing
curl -X POST http://localhost:5555/test/sheets/create
curl -X POST http://localhost:5555/test/sheets/process -d '{"sheet_url": "..."}'
```

### Phase 1: Core Integration (2-3 hours)
**Priority**: High - After sandbox validation
**Components**:
- [ ] Create Theodore Gmail account
- [ ] Set up OAuth2 authentication with Google Sheets API
- [ ] Implement basic `GoogleSheetsClient` class
- [ ] Create simple batch processor with parallel execution
- [ ] Add sheet structure validation

**Deliverables**:
- Working batch processor that can read company lists and update progress
- Basic error handling and retry logic

### Phase 2: Web Interface Integration (1-2 hours)
**Priority**: High  
**Components**:
- [ ] Add batch processing section to Theodore web interface
- [ ] Implement sheet URL validation and extraction
- [ ] Create real-time progress display
- [ ] Add batch job management (start/stop/status)

**Deliverables**:
- Complete user workflow from sheet URL to processed results
- Real-time progress tracking in web interface

### Phase 3: Advanced Features (1-2 hours)
**Priority**: Medium
**Components**:
- [ ] Enhanced error categorization and reporting
- [ ] Resume processing from failures
- [ ] Priority-based processing queue
- [ ] Batch job scheduling and queuing

**Deliverables**:
- Robust production-ready batch processing system
- Advanced error recovery and reporting

### Phase 4: Polish & Documentation (30 minutes)
**Priority**: Medium
**Components**:
- [ ] User documentation and examples
- [ ] Sample Google Sheet templates
- [ ] Performance optimization
- [ ] Comprehensive testing

**Deliverables**:
- Complete documentation for users
- Optimized and tested system

## 🔗 Integration with Existing Theodore Components

### Reuse Existing Systems
- **`src/main_pipeline.py`**: Core company research logic
- **`src/pinecone_client.py`**: Vector database storage
- **`src/progress_logger.py`**: Real-time progress tracking
- **`src/intelligent_company_scraper.py`**: Website analysis
- **`src/research_manager.py`**: Structured research prompts
- **All AI clients**: Bedrock, Gemini, OpenAI for analysis

### New Integration Points
- **Batch Progress Tracking**: Extend existing progress logger for batch operations
- **Sheet Updates**: Real-time status updates via Google Sheets API
- **Error Reporting**: Detailed error messages in sheet cells
- **Results Export**: Option to export full research data back to sheet

## 🎯 Success Metrics

### Technical Metrics
- **Throughput**: Process 50+ companies per hour
- **Reliability**: <5% failure rate under normal conditions
- **Performance**: Sheet updates within 30 seconds of status changes
- **Recovery**: Ability to resume processing after interruptions

### User Experience Metrics
- **Setup Time**: <2 minutes from sheet creation to processing start
- **Ease of Use**: No technical knowledge required beyond Google Sheets
- **Transparency**: Clear progress and error reporting
- **Flexibility**: Support for various sheet formats and sizes

## 📚 Documentation Requirements

### User Documentation
1. **Getting Started Guide**: Step-by-step sheet setup and sharing
2. **Sheet Template**: Pre-formatted Google Sheet for easy copying
3. **Troubleshooting**: Common issues and solutions
4. **Best Practices**: Optimal sheet structure and company naming

### Technical Documentation
1. **API Reference**: Google Sheets integration endpoints
2. **Configuration Guide**: Environment setup and authentication
3. **Error Codes**: Complete list of error types and meanings
4. **Performance Tuning**: Optimization settings and recommendations

## 🚀 Future Enhancements

### Potential Extensions
- **Scheduled Processing**: Automatic processing of sheets on schedule
- **Webhook Integration**: Real-time processing triggers
- **Advanced Filtering**: Process only companies matching criteria
- **Results Analytics**: Summary statistics and insights
- **Multi-Sheet Support**: Process multiple sheets in sequence
- **Export Options**: PDF reports, CSV exports, dashboard integration

### Scalability Considerations
- **Queue Management**: Redis-based job queue for high volume
- **Distributed Processing**: Multiple worker nodes for large batches
- **Caching**: Sheet structure and company data caching
- **Monitoring**: Detailed metrics and alerting for production use

## 🔬 Isolated Testing Sandbox Plan

### Engineering Manager Questions & Clarifications Needed:

**Architecture Questions:**
1. **API Endpoint Structure**: Should I create dedicated test endpoints like `/test/sheets/*` or build the actual production endpoints but test them in isolation?

2. **Credential Management**: How do you prefer to handle Google Sheets API credentials during testing?
   - Service account JSON file in testing directory? 
   - Environment variables specific to testing?
   - Separate test Google account vs production account?

3. **Testing Data Flow**: Should the sandbox:
   - Use real Google Sheets API but with test sheets?
   - Mock the Google Sheets API completely?
   - Hybrid approach - real API for auth testing, mocked for batch processing?

4. **Integration Points**: Which Theodore components should the sandbox use vs mock?
   - Real Pinecone database (separate test index)?
   - Real AI clients (Bedrock/Gemini) with test data?
   - Real company research pipeline vs mocked responses?

5. **Testing Server**: Should I run the test endpoints on:
   - Separate port (e.g., 5555) from main app (5002)?
   - Same Flask app with `/test/` routes?
   - Completely separate test server?

### Proposed Sandbox Structure:

```
testing_sandbox/sheets_integration/
├── README.md                           # Setup instructions
├── requirements_test.txt               # Isolated dependencies  
├── .env.test                          # Test environment variables
├── credentials/                        # Test credentials directory
│   └── test_service_account.json      # Google Sheets test credentials
├── test_server.py                     # Isolated Flask test server
├── test_sheets/                       # Test sheet templates
│   ├── sample_companies.csv           # Sample data
│   └── expected_results.json          # Expected outputs
├── cli_tools/                         # Standalone testing tools
│   ├── test_auth.py                   # Test Google Sheets authentication
│   ├── test_sheet_creation.py         # Test dual-sheet creation
│   ├── test_batch_processing.py       # Test company processing
│   └── test_field_mapping.py          # Test all 62+ field exports
├── api_tests/                         # API endpoint tests
│   ├── test_endpoints.py              # Automated API tests
│   ├── curl_examples.md               # Manual testing examples
│   └── postman_collection.json        # Postman test collection
├── mock_data/                         # Test data and mocks
│   ├── mock_company_data.py           # Fake CompanyData objects
│   ├── mock_sheets_responses.py       # Mock Google Sheets API
│   └── test_companies.json            # Sample company list
└── integration_tests/                 # End-to-end tests
    ├── test_full_workflow.py          # Complete workflow test
    └── test_error_scenarios.py        # Error handling tests
```

### Sandbox API Endpoints (Proposed):

```python
# Isolated test server on port 5555
GET  /test/health                      # Test server health
POST /test/auth/validate               # Test Google Sheets authentication
POST /test/sheets/create               # Create test dual-sheet structure
POST /test/sheets/validate             # Validate sheet structure
POST /test/sheets/process              # Process companies from sheet URL
GET  /test/sheets/status/<job_id>      # Get processing status
GET  /test/field-mapping/validate      # Test all 62+ field mappings
POST /test/company/mock-research       # Test single company processing
```

### Testing Workflow (Proposed):

```bash
# Step 1: Setup
cd testing_sandbox/sheets_integration
pip install -r requirements_test.txt
cp .env.test.example .env.test
# [User provides Google Sheets credentials]

# Step 2: Authentication testing
python cli_tools/test_auth.py

# Step 3: Sheet creation testing  
python cli_tools/test_sheet_creation.py --url "SHEET_URL"

# Step 4: Field mapping validation
python cli_tools/test_field_mapping.py

# Step 5: End-to-end batch processing
python cli_tools/test_batch_processing.py --sheet "SHEET_URL" --companies 3

# Step 6: API endpoint testing
python test_server.py &
curl http://localhost:5555/test/health
curl -X POST http://localhost:5555/test/sheets/process -d '{"sheet_url":"..."}'
```

## ✅ **FINAL SPECIFICATIONS (Engineering Manager Approved)**

### **Core Architecture Decisions:**
1. **Server Setup**: Same Flask app with `/isolated/sheets/*` routes
2. **Pinecone Index**: New test index `theodore-companies-test`
3. **Credentials**: Same environment variables, point to test resources
4. **Code Reuse**: Batch mode uses exact same company research pipeline (Option B - full workflow)

### **Batch Processing Specifications:**
- **Sheet Format**: Column A = Company Name, Column B = URL (with header row)
- **Header Validation**: Flexible - accept variations like "Company", "Website", etc.
- **URL Handling**: Optional - if empty, use Google Search to find website first
- **Concurrency**: 10 companies processed simultaneously
- **Error Handling**: Skip and continue, stop if 3 consecutive errors, reset counter on success
- **Progress Updates**: Update sheet every 5 companies
- **Duplicate Handling**: Always update (re-research existing companies)
- **Error Messages**: Full detailed error messages in sheet

### **Sheet Management:**
- **Dual-Sheet Creation**: Create both sheets if not present, update if existing
- **Batch Job Control**: Users can stop/cancel, no multiple batches, no resume
- **Progress Visibility**: Console logging with full details + sheet updates

### **Authentication & Testing:**
- **Theodore Email**: `theodore.salesbot@gmail.com`
- **Test Sheet**: https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit?usp=sharing
- **No Mocking**: Real Google Sheets API, real AI research, real everything
- **Isolated Testing**: Production code in isolation to avoid breaking main Theodore
- **Credentials File**: `/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/client_secret_1096944990043-5u1eohnobc583lvueqr2cvfvm9tcjc3p.apps.googleusercontent.com.json`
- **OAuth Client ID**: `1096944990043-5u1eohnobc583lvueqr2cvfvm9tcjc3p.apps.googleusercontent.com`
- **Project ID**: `theodore-462403`

### **Implementation Approach:**
- **Development**: Copy existing research code to test folder initially
- **Production**: Modify original code to handle both single and batch modes
- **Research Pipeline**: Full "Research this company" workflow per row
- **Data Storage**: Save results to both Pinecone and spreadsheet

---

## 🚀 **READY TO IMPLEMENT - Next Steps**

With all specifications finalized, the implementation order is:

### **Phase 1: Google Sheets Authentication & Access**
1. **Configure OAuth2 redirect URIs** in Google Cloud Console:
   - Add: `http://localhost:5002/auth/google/callback`
   - Add: `http://localhost:5555/auth/google/callback`
   - **IMPORTANT**: No trailing slashes (causes redirect_uri_mismatch errors)
2. **Create OAuth2 authentication flow** using existing credentials file
3. **Test basic read/write operations** on the provided test sheet
4. **Implement sheet structure validation** (flexible header detection)

### **Phase 2: Batch Processing Engine**
1. **Copy existing research pipeline** to isolated testing environment
2. **Build batch processor** with 10-concurrent processing
3. **Implement dual-sheet creation and updates** (Progress + Complete Data)
4. **Add error handling** (3 consecutive errors = stop, detailed error messages)

### **Phase 3: Integration & Testing**
1. **Add `/isolated/sheets/*` routes** to main Flask app
2. **Test end-to-end workflow** with provided test sheet
3. **Implement progress updates** (every 5 companies + console logging)
4. **Test error scenarios** and recovery

### **Phase 4: Production Integration**
1. **Modify original research code** to handle both single and batch modes
2. **Create new Pinecone test index** `theodore-companies-test`
3. **Add batch job control** (start/stop functionality)
4. **Final testing and documentation**

## 📋 **Implementation Checklist**

### **Prerequisites (Before Starting):**
- [x] Google Sheets credentials file available at: `/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/client_secret_1096944990043-5u1eohnobc583lvueqr2cvfvm9tcjc3p.apps.googleusercontent.com.json`
- [x] Test sheet shared with `theodore.salesbot@gmail.com`: https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit?usp=sharing
- [ ] **REQUIRED**: Add redirect URIs to Google Cloud Console (NO trailing slashes):
  - `http://localhost:5002/auth/google/callback`
  - `http://localhost:5555/auth/google/callback`

### **Implementation Tasks:**
- [ ] OAuth2 authentication implementation using provided credentials
- [ ] Test sheet read/write access with proper authentication
- [ ] Batch processor with 10-concurrent processing
- [ ] Dual-sheet creation (Progress Tracking + Complete Research Data)
- [ ] Error handling (3 consecutive = stop, reset on success)
- [ ] Progress updates (every 5 companies)
- [ ] Full error message reporting in sheets
- [ ] Console logging with details
- [ ] `/isolated/sheets/*` Flask routes in main app
- [ ] Pinecone test index `theodore-companies-test` creation
- [ ] Integration with existing research pipeline (full Option B workflow)
- [ ] Flexible header detection (Company Name/URL variations)
- [ ] Google Search integration for missing URLs

## 🔧 **Technical Implementation Notes**

### **OAuth2 Redirect URI Research Findings:**
- **Critical**: Google OAuth2 requires exact matching - NO trailing slashes
- **Common Error**: `redirect_uri_mismatch` caused by trailing slash mismatches
- **Google Cloud Console**: Doesn't allow trailing slashes in redirect URIs anyway
- **Best Practice**: Use `http://localhost:PORT/path` format (no trailing `/`)

### **Development Environment Setup:**
- **Main App Port**: 5002 (existing Theodore application)
- **Test Routes**: `/isolated/sheets/*` added to main Flask app
- **Concurrency**: 10 companies processed simultaneously
- **Error Threshold**: Stop after 3 consecutive errors, reset counter on success
- **Progress Updates**: Every 5 companies + detailed console logging

### **Integration Strategy:**
- **Development Phase**: Copy existing research code to isolated environment
- **Production Phase**: Modify original code to handle both single and batch modes
- **Research Pipeline**: Use full "Research this company" workflow (Option B)
- **Data Storage**: Dual storage - Pinecone + Google Sheets export

---

This plan provides a complete roadmap for implementing Google Sheets batch processing with all specifications documented and approved. **Ready to begin implementation after redirect URIs are configured in Google Cloud Console.**