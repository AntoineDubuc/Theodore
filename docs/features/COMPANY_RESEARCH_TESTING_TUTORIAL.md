# Theodore v2 CLI Testing Tutorial
## How to Test Theodore's Advanced Command-Line Interface

This tutorial shows you how to test Theodore's **v2 CLI system** - the next-generation command-line interface for AI-powered company intelligence.

---

## 🎯 **What You're Testing Now**

The **Theodore v2 CLI System** includes:
- 🚧 **Advanced CLI Architecture** (Clean Architecture with DDD principles)
- 🚧 **Multi-Command Interface** (research, discover, batch, config, export, plugin)
- 🚧 **Real-time Progress Tracking** (Rich terminal interfaces with progress bars)
- 🚧 **Multiple Output Formats** (table, JSON, YAML, markdown)
- 🚧 **Dependency Injection Container** (Enterprise-grade modularity)
- 🚧 **MCP Integration** (Multiple AI search providers)

**⚠️ IMPORTANT: v2 CLI is in EARLY DEVELOPMENT. Most commands are temporarily disabled due to import issues.**

---

## 📁 **Location & Setup**

### **Navigate to Theodore v2**
```bash
cd /Users/antoinedubuc/Desktop/AI_Goodies/Theodore/v2
```

### **Install v2 CLI**
```bash
# Install in development mode
pip install -e .

# OR run directly without installation
python3 src/cli/entry_point.py --help
```

---

## 🚀 **Method 1: Basic CLI Testing (Currently Working)**

### **Test CLI Installation**
```bash
# Test basic CLI functionality
python3 src/cli/entry_point.py test

# Check CLI help
python3 src/cli/entry_point.py --help

# Check version
python3 src/cli/entry_point.py --version
```

### **Expected Output:**
```
✅ Theodore v2 CLI is working!
🏗️ Full commands temporarily disabled to fix import issues
```

---

## 🧪 **Method 2: Architecture Testing**

### **Test Core Components**
```bash
# Test container initialization
python3 -c "from src.infrastructure.container.application import ApplicationContainer; print('Container OK')"

# Test CLI framework
python3 -c "from src.cli.main import cli; print('CLI Framework OK')"

# Test domain models
python3 -c "from src.core.domain.entities.company import Company; print('Domain Models OK')"
```

### **Test Configuration System**
```bash
# Test settings loading
python3 -c "from src.infrastructure.config.settings import Settings; print('Settings OK')"

# Test secure storage
python3 -c "from src.infrastructure.config.secure_storage import SecureStorage; print('Secure Storage OK')"
```

---

## 🔍 **Method 3: Planned CLI Commands (Future)**

### **Research Commands** (TICKET-020)
```bash
# Research single company
theodore research "Apple Inc" --output json --save results.json

# Research with specific website
theodore research "Salesforce" "salesforce.com" --verbose

# Research with configuration overrides
theodore research "Microsoft" --config-override "timeout=120" --no-domain-discovery
```

### **Discovery Commands** (TICKET-021)
```bash
# Discover similar companies
theodore discover "Salesforce" --business-model saas --limit 10

# Interactive discovery
theodore discover "Microsoft" --interactive --research-discovered

# Advanced filtering
theodore discover "Stripe" --industry fintech --company-size medium --save results.yaml
```

### **Batch Processing** (TICKET-022)
```bash
# Batch research from CSV
theodore batch research companies.csv --concurrency 5 --output-dir ./results

# Job management
theodore batch list-jobs
theodore batch status <job-id>
theodore batch cancel <job-id>
```

### **Configuration Management**
```bash
# Initialize configuration
theodore config init

# Set configuration values
theodore config set gemini_api_key=AIza...

# Show current configuration
theodore config show --validate
```

### **Export & Data Management**
```bash
# Export company data
theodore export companies --format csv --since 7d

# Export research history
theodore export research-history --format json
```

---

## 📊 **Understanding v2 CLI Architecture**

### **Clean Architecture Layers:**
```
┌─────────────────────────────────────────┐
│              CLI Layer                  │
│  (Click commands, Rich formatting)     │
├─────────────────────────────────────────┤
│           Application Layer             │
│  (Use cases, workflows, validation)    │
├─────────────────────────────────────────┤
│            Domain Layer                 │
│  (Entities, value objects, services)   │
├─────────────────────────────────────────┤
│          Infrastructure Layer           │
│  (AI clients, web scrapers, storage)   │
└─────────────────────────────────────────┘
```

### **Key Features (Planned):**
- **Multi-Provider AI Integration**: Gemini, AWS Bedrock, OpenAI with failover
- **Intelligent Web Scraping**: 4-phase extraction with AI-driven page selection
- **Advanced Similarity Discovery**: Vector-based search with multi-dimensional scoring
- **Real-time Progress Tracking**: Rich terminal interfaces with live updates
- **Comprehensive Output Formats**: Table, JSON, YAML, markdown with customization
- **Plugin System**: Extensible architecture for custom functionality

---

## 📈 **Current Development Status**

### **✅ Working Components:**
- Basic CLI structure with Click framework
- Configuration system with Pydantic settings
- Domain models and entity definitions
- Rich terminal formatting and progress tracking
- Entry point and help system
- Test framework structure

### **🚧 In Development:**
- Main command implementations (research, discover, batch)
- Dependency injection container wiring
- AI provider integrations
- MCP search tool adapters
- Plugin system architecture

### **🔧 Known Issues:**
- Import circular dependencies in main.py
- Container initialization needs debugging
- Some infrastructure adapters missing
- Limited integration testing
- Plugin system not yet implemented

---

## 🎯 **Test Cases to Try**

### **Basic CLI Tests:**
```bash
# Test CLI help system
python3 src/cli/entry_point.py --help
python3 src/cli/entry_point.py test

# Test version information
python3 src/cli/entry_point.py --version

# Test verbose mode
python3 src/cli/entry_point.py --verbose test
```

### **Configuration Tests:**
```bash
# Test configuration loading
python3 -c "from src.infrastructure.config.settings import Settings; s = Settings(); print(f'Config loaded: {s.dict()}')"

# Test secure storage
python3 -c "from src.infrastructure.config.secure_storage import SecureStorage; print('Secure storage available')"
```

### **Architecture Tests:**
```bash
# Test domain entities
python3 -c "from src.core.domain.entities.company import Company; c = Company(name='Test', website_url='test.com'); print(f'Company: {c.name}')"

# Test value objects
python3 -c "from src.core.domain.value_objects.ai_config import AIConfig; print('AI Config available')"
```

---

## 📄 **Test Output Locations**

### **Configuration Files**
```bash
# Configuration examples
ls config/
cat config/theodore.yml.example

# Configuration schemas
ls config/schemas/
```

### **Test Results**
```bash
# Unit test results
cat test_results.json

# Integration test results
cat container_test_results.json
cat cli_test_results.json

# Comprehensive test reports
python3 tests/comprehensive_test_report.py
```

### **Development Logs**
```bash
# Check development logs
tail -f logs/development.log

# View test execution logs
cat tests/integration/test_reports/
```

---

## 🔧 **Development & Testing**

### **Run Test Suite**
```bash
# Run all tests
python3 run_tests.py

# Run specific test categories
python3 -m pytest tests/unit/ -v
python3 -m pytest tests/integration/ -v

# Run CLI-specific tests
python3 -m pytest tests/cli/ -v
```

### **Manual Testing**
```bash
# Test container initialization
python3 tests/container_integration_test.py

# Test CLI commands
python3 tests/simple_cli_test.py

# Test comprehensive flow
python3 tests/integration/test_comprehensive_flow.py
```

### **QA and Validation**
```bash
# Run quality assurance
python3 run_qa.py

# Generate comprehensive reports
python3 tests/comprehensive_test_report.py
```

---

## 🚨 **Common Issues & Solutions**

### **Issue: "Import Error" when testing CLI**
```bash
# Solution: Add v2/src to Python path
export PYTHONPATH=/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/v2/src:$PYTHONPATH
python3 src/cli/entry_point.py test
```

### **Issue: "Container initialization failed"**
```bash
# Solution: Check dependency injection setup
python3 -c "from src.infrastructure.container.application import ApplicationContainer; print('Container check')"
```

### **Issue: "Configuration not found"**
```bash
# Solution: Copy example configuration
cp config/theodore.yml.example ~/.theodore/config.yml
# Edit with your API keys
```

### **Issue: "Commands not available"**
```bash
# Expected: Most commands are temporarily disabled
# Solution: Only 'test' command works currently
python3 src/cli/entry_point.py test
```

---

## 🎊 **You're Testing Enterprise-Grade CLI Architecture!**

Unlike the main Theodore system, **the v2 CLI represents**:

- 🏗️ **Enterprise Architecture** with clean separation of concerns
- 📦 **Dependency Injection** for testability and modularity
- 🚀 **Async-First Design** for high performance
- 🛡️ **Type Safety** with Pydantic and comprehensive validation
- 🔌 **Plugin System** for extensibility
- 📊 **Rich Terminal Experience** with progress tracking and formatting

**This is Theodore's future - a professional, enterprise-ready CLI for AI-powered company intelligence!**

---

## 📞 **Need Help?**

- **v2 Documentation:** Check `docs/` directory
- **Technical Specs:** `TECHNICAL_SPECIFICATION.md`
- **Architecture Guide:** `TECHNICAL_ARCHITECTURE_DOCUMENT.md`
- **Test Reports:** `tests/integration/test_reports/`
- **Development Tickets:** `tickets/` directory

**Happy v2 CLI Testing! 🚀✨**

---

## 📊 **Understanding Theodore's Research Process**

### **Phase 1: Link Discovery** 🔍
- Reads `robots.txt` for additional paths
- Parses `sitemap.xml` for structured navigation
- Performs recursive crawling (3 levels deep)
- Discovers up to 1000 links from the website

### **Phase 2: LLM Page Selection** 🎯
- AI analyzes all discovered links
- Prioritizes pages with contact, about, team, career info
- Selects 10-50 most valuable pages for extraction
- Targets missing data fields intelligently

### **Phase 3: Content Extraction** 📄
- Parallel processing of selected pages (10 concurrent)
- Clean content extraction (removes nav, footer, scripts)
- Processes 5-50 pages in ~5 seconds
- Extracts main content while preserving structure

### **Phase 4: AI Analysis** 🧠
- Gemini 2.5 Pro with 1M token context
- Combines content from all scraped pages
- Generates structured business intelligence
- Creates sales-ready company summaries

---

## 📈 **What Theodore Extracts**

### **Successfully Extracts (High Success Rate):**
- ✅ **Company descriptions** and value propositions
- ✅ **Business models** (B2B/B2C classification)
- ✅ **Industry** and market segments
- ✅ **Technical sophistication** assessments
- ✅ **Company size** and stage indicators
- ✅ **Competitive positioning**
- ✅ **Products/services** and offerings
- ✅ **Target markets** and customer segments

### **Challenging Fields (Improvement Needed):**
- 🔧 **Founding years** (often in timeline graphics)
- 🔧 **Physical locations** (complex footer parsing)
- 🔧 **Employee counts** (typically not published)
- 🔧 **Contact details** (behind forms)
- 🔧 **Social media links** (complex footer structures)
- 🔧 **Leadership teams** (separate page navigation)

---

## 🎯 **Test Cases to Try**

### **Easy Companies (High Success Expected):**
```bash
# Well-structured websites with clear information
- Apple Inc
- Microsoft
- Google
- Salesforce
- Shopify
- HubSpot
```

### **Medium Difficulty:**
```bash
# More complex sites but still extractable
- Tesla
- Airbnb
- Spotify
- Netflix
- Slack
```

### **Challenging Cases:**
```bash
# Complex sites, good for testing limits
- Amazon (massive, complex structure)
- General Electric (corporate complexity)
- IBM (enterprise focus)
- Oracle (technical complexity)
```

---

## 📄 **Test Output Locations**

### **Real-Time Progress Logs**
```bash
# View live processing logs
tail -f app.log

# Check processing progress
cat logs/processing_progress.json
```

### **Research Results Storage**
```bash
# Pinecone vector database (check via web interface)
http://localhost:5002/api/database

# Exported data files
ls data/exports/

# Company detail files
ls data/company_details/
```

### **Test Result Files**
```bash
# Test outputs from direct testing
ls tests/sandbox/testing_sandbox/

# Development test results  
ls tests/development/
```

---

## 🔧 **Advanced Testing Options**

### **Test Different AI Models**
```bash
# Test with different models (modify in app.py or config)
# - Gemini 2.5 Pro (primary)
# - Nova Pro (cost-optimized)
# - OpenAI GPT-4o-mini (fallback)
```

### **Test Batch Processing**
```bash
# Process multiple companies from Google Sheets
python scripts/batch/batch_process_google_sheet.py

# Test batch processing with CSV
python scripts/batch/process_google_sheet_first_10.py
```

### **Test Similarity Discovery**
```bash
# Find companies similar to a known company
python test_similarity_engine.py

# Test the discovery system
python src/experimental/v2_discovery.py
```

---

## 🎭 **Testing Scenarios**

### **Scenario 1: New Company Research**
1. Choose a company not in your database
2. Enter it in the web interface
3. Watch the 4-phase process
4. Evaluate the quality of extracted data
5. Check if it gets stored in Pinecone

### **Scenario 2: Similarity Discovery**
1. Research a well-known company (e.g., "Salesforce")
2. Use the "Find Similar" feature
3. Review the similar companies found
4. Evaluate the quality of matches

### **Scenario 3: Batch Processing**
1. Create a CSV with 5-10 company names
2. Use the batch processing feature
3. Monitor progress and results
4. Review the comprehensive output

### **Scenario 4: API Integration**
1. Test the API endpoints directly
2. Integrate with curl or Postman
3. Verify JSON response formats
4. Test error handling

---

## 🏆 **Success Indicators**

### **✅ Research Process Working:**
- All 4 phases complete without errors
- 15-50 pages discovered and processed
- 5-10 seconds total processing time
- Structured business intelligence generated

### **✅ Data Quality Good:**
- Accurate company description (not generic)
- Correct industry classification
- Realistic business model assessment
- Meaningful competitive analysis

### **✅ System Performance:**
- Processing completes in under 30 seconds
- No timeout errors
- Real-time progress updates working
- Results properly stored in database

---

## 🚨 **Common Issues & Solutions**

### **Issue: "No results found"**
```bash
# Solution: Check if the company has a website
# Try with "Company Name + website" or use full domain
```

### **Issue: "Processing timeout"**
```bash
# Solution: Check app.log for specific errors
tail -f app.log

# Restart the application
pkill -f "python3 app.py"
python3 app.py
```

### **Issue: "AI analysis failed"**
```bash
# Solution: Check API credentials
python test_credentials.py

# Verify model availability
python tests/test_real_ai.py
```

### **Issue: "Pinecone connection failed"**
```bash
# Solution: Check Pinecone credentials and index
python scripts/check_pinecone_database.py
```

---

## 🎊 **You're Testing Real Company Intelligence!**

Unlike the v2 infrastructure tests, **this is the actual Theodore system** that:

- ✅ **Gathers real company data** from live websites
- ✅ **Uses sophisticated AI analysis** with 1M token context
- ✅ **Processes 10-50 pages per company** in seconds
- ✅ **Generates business intelligence** for sales teams
- ✅ **Stores results in vector database** for similarity search
- ✅ **Provides real-time progress tracking** during research

**This is Theodore's core value proposition - AI-powered company intelligence gathering!**

---

## 📞 **Need Help?**

- **Web Interface:** http://localhost:5002
- **Settings Page:** http://localhost:5002/settings  
- **Database View:** http://localhost:5002/api/database
- **Logs:** `tail -f app.log`
- **Test Files:** Check `tests/sandbox/testing_sandbox/`

**Happy Company Research Testing! 🕵️‍♂️✨**