# 🚀 Theodore Developer Onboarding Guide

Welcome to Theodore - AI-Powered Company Intelligence System! This guide will get you up and running quickly with the **clean, reorganized codebase**.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [System Architecture](#system-architecture) 
3. [Core Features & Code Flow](#core-features--code-flow)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Common Tasks](#common-tasks)
7. [Troubleshooting](#troubleshooting)

---

## 🏃 Quick Start

### Prerequisites
- Python 3.9+
- Required API keys (see Environment Setup)

### 1. Installation
```bash
# Clone and navigate to the project
cd Theodore

# Set up virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
# Copy the environment template
cp .env.example .env

# Configure your API keys in .env:
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=theodore-companies
GEMINI_API_KEY=your_gemini_key  # Optional but recommended
```

### 3. Start the Application
```bash
# Start the main web application
python3 app.py

# Access the UI at: http://localhost:5002
# Settings page: http://localhost:5002/settings
```

### 4. Verify Installation
1. Open http://localhost:5002 in your browser
2. Try the "Quick Demo" button in the Discovery tab
3. Check that all tabs load (Discovery, Process, Database, Batch)

---

## 🏗️ System Architecture

Theodore is built as a modern web application with a clean separation between frontend and backend:

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (Flask)                    │
│     Templates + Static Files + JavaScript                  │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/API calls
┌─────────────────────▼───────────────────────────────────────┐
│                  Core Backend (src/)                       │
│    main_pipeline.py + intelligent_company_scraper.py       │
└─────────────────────┬───────────────────────────────────────┘
                      │ Data flow
┌─────────────────────▼───────────────────────────────────────┐
│               External Services                             │
│    AWS Bedrock + Pinecone + Gemini AI + Crawl4AI          │
└─────────────────────────────────────────────────────────────┘
```

### Core Directory Structure
```
Theodore/
├── 🎯 CORE APPLICATION
│   ├── app.py                          # Main Flask web application
│   ├── templates/                      # HTML templates
│   │   ├── index.html                  # Main UI (4 tabs)
│   │   └── settings.html               # Settings page
│   └── static/                         # CSS/JS/Assets
│       ├── css/style.css               # Main styles
│       └── js/app.js                   # Frontend logic
│
├── 🧠 CORE BACKEND
│   └── src/
│       ├── main_pipeline.py            # Main orchestration
│       ├── models.py                   # Pydantic data models
│       ├── intelligent_company_scraper.py  # 4-phase scraper
│       ├── simple_enhanced_discovery.py    # Similarity search
│       ├── bedrock_client.py           # AWS AI client
│       ├── pinecone_client.py          # Vector database
│       ├── gemini_client.py            # Google AI client
│       ├── openai_client.py            # OpenAI fallback
│       └── progress_logger.py          # Real-time progress
│
├── ⚙️ CONFIGURATION
│   └── config/
│       ├── settings.py                 # Centralized config
│       └── credentials/                # Service account files
│
├── 🗂️ ORGANIZED RESOURCES  
│   ├── src/experimental/               # Experimental features
│   ├── src/legacy/                     # Legacy implementations
│   ├── tests/                          # Test files
│   ├── scripts/                        # Utility scripts
│   └── docs/                           # Documentation
```

---

## 🎯 Core Features & Code Flow

Theodore has **4 main functional features** accessible through the web UI:

### 1. 🔍 Company Discovery (Similarity Search)

**What it does:** Find companies similar to a given company using AI-powered similarity analysis.

**Code Flow:**
```
UI: Discovery Tab → JavaScript: handleDiscovery() → 
API: POST /api/discover → Backend: SimpleEnhancedDiscovery → 
Pinecone: Vector search → Results displayed
```

**Key Files:**
- Frontend: `static/js/app.js` (handleDiscovery function)
- Backend: `app.py` (discover_similar_companies route)
- Core Logic: `src/simple_enhanced_discovery.py`

### 2. ➕ Company Processing (4-Phase Intelligent Scraping)

**What it does:** Add new companies to the database with comprehensive AI-powered data extraction.

**Code Flow:**
```
UI: Process Tab → JavaScript: handleProcessing() → 
API: POST /api/process-company → Backend: IntelligentCompanyScraperSync →
4 Phases: Link Discovery → Page Selection → Content Extraction → AI Aggregation →
Pinecone: Store with embeddings → Success response
```

**The 4-Phase System:**
1. **Link Discovery**: Find up to 1000 URLs via robots.txt, sitemaps, recursive crawling
2. **LLM Page Selection**: AI chooses 10-50 most valuable pages for data extraction  
3. **Parallel Content Extraction**: Concurrent scraping of selected pages
4. **AI Aggregation**: Gemini 2.5 Pro combines all content into business intelligence

**Key Files:**
- Frontend: `static/js/app.js` (handleProcessing function)
- Backend: `app.py` (process_company route)
- Core Logic: `src/intelligent_company_scraper.py`
- Progress: `src/progress_logger.py`

### 3. 🗄️ Database Browser

**What it does:** View, manage, and interact with the stored company database.

**Code Flow:**
```
UI: Database Tab → JavaScript: refreshDatabase() → 
API: GET /api/companies → Backend: Pinecone queries → 
Display company table with actions
```

**Key Files:**
- Frontend: `static/js/app.js` (refreshDatabase, addSampleCompanies, clearDatabase)
- Backend: `app.py` (multiple database routes)
- Core Logic: `src/pinecone_client.py`

### 4. ⚙️ Settings Management

**What it does:** Configure system settings, AI models, and view system status.

**Code Flow:**
```
UI: /settings → Backend: settings route → 
Template: settings.html → Configuration management
```

**Key Files:**
- Frontend: `templates/settings.html`
- Backend: `app.py` (settings routes)
- Config: `config/settings.py`

---

## 🔄 Development Workflow

### Common Development Tasks

#### Adding a New Feature
1. **Identify the layer:** Frontend-only, Backend-only, or Full-stack
2. **Frontend changes:** Modify `templates/index.html` and `static/js/app.js`
3. **Backend changes:** Add routes to `app.py` and logic to `src/` modules
4. **Test thoroughly:** Use both automated tests and manual UI testing

#### Modifying the Scraping System
1. **Core scraper:** Edit `src/intelligent_company_scraper.py`
2. **Data models:** Update `src/models.py` if needed
3. **Test with real companies:** Use `python test_real_company.py`

#### Adding New API Endpoints
1. **Add route:** In `app.py` with proper error handling
2. **Update frontend:** Add corresponding JavaScript in `app.js`
3. **Test the API:** Use curl or the browser dev tools

#### Modifying AI Clients
1. **AWS/Bedrock:** Edit `src/bedrock_client.py`
2. **Google/Gemini:** Edit `src/gemini_client.py`  
3. **OpenAI:** Edit `src/openai_client.py`

### Code Style Guidelines
- **No comments unless necessary** - Code should be self-documenting
- **Follow existing patterns** - Match the style of surrounding code
- **Use type hints** - Leverage Pydantic models for data validation
- **Error handling** - Always provide meaningful error messages to users

---

## 🧪 Testing

### Test Organization
```
tests/
├── test_api_endpoint.py        # API testing
├── test_similarity_engine.py   # Core functionality tests  
├── test_real_ai.py            # AI integration tests
├── run_similarity_tests.py    # Test runner
├── legacy/                    # Old/deprecated tests
└── sandbox/                   # Development testing area
```

### Running Tests
```bash
# Run core tests
python tests/test_api_endpoint.py
python tests/test_similarity_engine.py

# Test with real companies (requires API keys)
python tests/test_real_ai.py

# Run specific test scenarios
python tests/run_similarity_tests.py
```

### Manual Testing Checklist
After making changes, always test these core workflows:

1. **Start Application:**
   ```bash
   python3 app.py
   # Should start without errors on http://localhost:5002
   ```

2. **Discovery Tab:**
   - Enter a company name (try "Stripe" or "Linear")
   - Click "Discover Similar Companies"  
   - Verify results are displayed

3. **Process Tab:**
   - Enter company name and website
   - Click "Generate Sales Intelligence"
   - Watch 4-phase progress updates
   - Verify success message and results

4. **Database Tab:**
   - Click "Refresh" button
   - Verify companies are listed
   - Try "Add Sample Companies"

5. **Settings Page:**
   - Visit http://localhost:5002/settings
   - Verify all sections load properly

---

## 🛠️ Common Tasks

### Adding a New Company Field
1. **Update the data model** in `src/models.py`:
   ```python
   class CompanyData(BaseModel):
       # Add your new field
       new_field: Optional[str] = Field(None, description="Description")
   ```

2. **Update the scraper** in `src/intelligent_company_scraper.py` to extract the field

3. **Update the UI** in `templates/index.html` to display the field

### Modifying AI Prompts
1. **Scraping prompts:** Edit `src/intelligent_company_scraper.py`
2. **Discovery prompts:** Edit `src/simple_enhanced_discovery.py`
3. **Legacy prompts:** Check `src/legacy/` directory

### Database Operations
```bash
# Check database contents
python scripts/check_pinecone_database.py

# Clear all data (careful!)
python scripts/clear_pinecone.py

# Add test data
python scripts/add_test_companies_with_similarity.py
```

### Adding New Dependencies
1. **Install the package:** `pip install package_name`
2. **Update requirements:** `pip freeze > requirements.txt`
3. **Test:** Ensure the app still starts and works

---

## 🐛 Troubleshooting

### Application Won't Start
```bash
# Check for import errors
python3 -c "import app; print('✅ App imports successfully')"

# Check environment variables
python3 test_credentials.py

# View startup logs
tail -f app.log
```

### Scraping Issues
- **Timeouts:** Check website complexity and adjust timeouts in scraper
- **No content:** Verify the website allows scraping (robots.txt)
- **AI errors:** Check API keys and rate limits

### Database Issues
- **No results:** Verify Pinecone API key and index name
- **Import errors:** Check environment variables
- **Slow queries:** Check Pinecone index health

### UI Issues
- **JavaScript errors:** Check browser console
- **API failures:** Check network tab in browser dev tools
- **Styling issues:** Clear browser cache

### Getting Help

1. **Check logs:** Look in `app.log` and console output
2. **Review documentation:** Check files in `docs/` directory
3. **Test individual components:** Use files in `tests/` directory
4. **Check the backup:** Reorganization created a backup if you need to revert

---

## 🎯 Key Development Principles

### Focus on Core Functionality
- The 4 main UI features should always work perfectly
- Experimental features are in `src/experimental/` - don't break core for experiments
- Legacy features are in `src/legacy/` - reference only, don't add dependencies

### Maintain Performance
- Use concurrent processing where possible (scraper does this)
- Implement proper caching (Crawl4AI handles this)
- Monitor API costs (especially for AI calls)

### User Experience First
- Provide real-time progress updates for long operations
- Show meaningful error messages, not stack traces
- Make the UI responsive and accessible

### Code Quality
- Keep the main `app.py` focused on HTTP routing and responses
- Put business logic in `src/` modules
- Use Pydantic models for data validation
- Write self-documenting code

---

## 🚀 Ready to Contribute!

You now have everything you need to start developing with Theodore:

1. ✅ **Environment set up** - App running locally
2. ✅ **Architecture understood** - Know how data flows  
3. ✅ **Core features mapped** - Know where to make changes
4. ✅ **Testing strategy** - Can verify your changes work
5. ✅ **Common tasks** - Know how to extend the system

**Next steps:**
- Try the "Quick Demo" feature to see the system in action
- Make a small change and test it
- Check out the experimental features in `src/experimental/`
- Read through the existing code to understand the patterns

Happy coding! 🎉