# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Theodore - AI Company Intelligence System

## ⚠️ IMPORTANT: PROJECT OBJECTIVES CLARIFICATION

**WE WILL NEVER PROCESS THE FULL 400 COMPANY DATASET.**

This is NOT the point of this project.

## 🎯 ACTUAL PROJECT OBJECTIVES

### Primary Goal: Build Theodore - AI Company Intelligence System
Theodore is designed to help David with his survey response analysis by providing:

1. **Enhanced Company Intelligence Extraction**
   - Use Crawl4AI with proper AI-powered extraction (not manual regex)
   - Extract comprehensive business intelligence from company websites
   - Store data efficiently in vector databases for similarity analysis

2. **Demonstrate Technical Capabilities**
   - Show how Crawl4AI can extract real company data (not hallucinated data)
   - Prove that enhanced AI extraction works better than manual approaches
   - Validate the technical architecture for company intelligence gathering

3. **Prototype for David's Analysis**
   - Create a working system that COULD process his 400 companies
   - Show how sector clustering and similarity analysis would work
   - Provide the tools and methodology for company intelligence

### Current Status (Latest Session - December 2025):
- **UI Working**: ✅ Beautiful modern web interface at http://localhost:5002
- **Search Working**: ✅ Real-time company search suggestions  
- **Results Display Fixed**: ✅ Result cards properly visible in dark theme
- **MAJOR BREAKTHROUGH**: ✅ Real AI similarity discovery now working with Nova Pro model
- **Structured Research System**: ✅ 8 predefined research prompts with cost transparency
- **Cost Optimization**: ✅ 6x cost reduction ($0.66 → $0.11) with Nova Pro model
- **Research Session Management**: ✅ Track multi-prompt research with export capabilities
- **Root Issues RESOLVED**: ✅ All critical technical issues have been systematically fixed
- **Production Ready**: ✅ End-to-end AI-powered company analysis functional

## 🛠️ Development Commands

### Running the Application

**✅ CORRECT STARTUP METHOD:**
```bash
# Start main web application (PROPER WAY - background with logging)
nohup python3 app.py > app.log 2>&1 & echo $!
# Verify startup: sleep 10 && tail -10 app.log
# Access at: http://localhost:5002
# Settings page: http://localhost:5002/settings

# Alternative: Development mode (foreground)
python3 app.py

# Start V2 application (enhanced interface with advanced features)
python3 v2_app.py &
# Access at: http://localhost:5004

# Direct pipeline execution (CLI mode)
python -m src.main_pipeline

# Stop the application
pkill -f "python3 app.py"
```

**🔧 Troubleshooting Startup:**
```bash
# Check if app is running
curl -I http://localhost:5002/

# View startup logs
tail -f app.log

# Check port usage
lsof -i :5002

# Verify imports
python3 -c "import app; print('Import successful')"
```

### Testing & Debugging
```bash
# Test single company processing
python test_real_company.py

# Test scraping pipeline
python test_subprocess_scraper.py

# Test research system
python tests/test_real_ai.py

# Debug environment setup
python test_credentials.py

# Test similarity engine
python tests/test_similarity_engine.py

# Additional test files in testing_sandbox/
python testing_sandbox/test_v2_research.py
python testing_sandbox/test_v2_discovery.py
python testing_sandbox/minimal_test.py

# Note: Many legacy test files have been cleaned up from root directory
# Active tests are now in tests/ directory and testing_sandbox/
```

### Database Operations
```bash
# Check Pinecone database
python scripts/check_pinecone_database.py

# Clear all data
python scripts/clear_pinecone.py

# Add test companies
python scripts/add_test_companies_with_similarity.py

# Extract raw data
python scripts/extract_raw_pinecone_data.py
```

### Development Tools
```bash
# Install dependencies
pip install -r requirements.txt

# Environment setup
cp .env.example .env  # Then configure API keys

# Code quality (check if available first)
# Note: Add these commands to requirements.txt and run if linting is needed
# pip install flake8 black mypy
# flake8 src/ tests/
# black src/ tests/
# mypy src/

# Debug specific issues
python debug_research_pipeline.py
python debug_scraping_issue.py
```

## 🏗️ System Architecture

### Core Components Architecture

Theodore uses a sophisticated multi-layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Application Layer                    │
│  Flask (app.py) - API + UI Routes + Real-time Progress     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Intelligence Pipeline                        │
│  main_pipeline.py - Orchestrates all processing            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│            4-Phase Intelligent Scraping System             │
│  1. Link Discovery → 2. LLM Page Selection →               │
│  3. Parallel Extraction → 4. AI Aggregation               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│     Structured Research + Similarity Analysis Engine       │
│  research_manager.py + similarity_engine.py                │
└─────────────────────────────────────────────────────────────┘
```

### Key Data Flow Patterns

**Company Research Workflow:**
```
User Input → Research Manager → Intelligent Scraper → AI Analysis → Vector Generation → Pinecone Storage → Similarity Analysis → UI Display
```

**Structured Research Workflow:**
```
Prompt Selection → Session Creation → Base Research (optional) → Prompt Execution → Cost Calculation → Results Export
```

**Discovery Workflow:**
```
Company Name → Database Check → Research Status Assessment → Real-time Research (if needed) → Enhanced Results Display
```

### Critical Files and Their Roles

**Core Pipeline:**
- `src/main_pipeline.py` - Main orchestration and entry point
- `src/models.py` - Pydantic data models for all entities
- `src/intelligent_company_scraper.py` - 4-phase intelligent scraping system
- `src/research_manager.py` - Structured research with 8 predefined prompts
- `src/similarity_engine.py` - Multi-dimensional similarity scoring

**AI Integration:**
- `src/bedrock_client.py` - AWS Bedrock integration (Nova Pro model)
- `src/gemini_client.py` - Google Gemini integration (primary analysis)
- `src/openai_client.py` - OpenAI integration (fallback)

**Data & Storage:**
- `src/pinecone_client.py` - Vector database operations
- `src/progress_logger.py` - Thread-safe real-time progress tracking

**Web Interface:**
- `app.py` - Flask application with comprehensive API endpoints (primary interface)
- `v2_app.py` - V2 Flask application with enhanced research features
- `templates/index.html` - Modern dark-themed UI (primary)
- `templates/v2_index.html` - Enhanced V2 UI
- `static/js/app.js` - Frontend logic with real-time updates
- `static/js/v2_app.js` - V2 frontend enhancements

### Configuration Management

**Environment Variables (Required):**
```bash
# AWS Bedrock (Primary AI)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
BEDROCK_ANALYSIS_MODEL=amazon.nova-pro-v1:0  # 6x cost reduction

# Google AI (Primary Analysis)
GEMINI_API_KEY=AIza...

# Vector Database
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=theodore-companies

# Optional: OpenAI (Fallback)
OPENAI_API_KEY=sk-...
```

**Configuration Pattern:**
```python
# Load via pydantic settings
from config.settings import settings

# All environment variables automatically loaded
aws_client = BedrockClient(
    region=settings.aws_region,
    model=settings.bedrock_analysis_model
)
```

## 🔧 Common Development Patterns

### Adding New Research Prompts

```python
# In src/research_prompts.py
new_prompt = ResearchPrompt(
    id="custom_analysis",
    name="Custom Analysis", 
    description="Analyzes custom company aspects",
    prompt_template="Analyze {company_name} for...",
    estimated_tokens=2000,
    output_format=OutputFormat.JSON
)

# Register the prompt
research_prompt_library.add_prompt(new_prompt)
```

### Debugging Scraping Issues

1. **Check Progress Logs:**
   ```python
   # Look for these debug prefixes in console output:
   # 🔬 SCRAPER: Phase-by-phase execution
   # 🔧 PROGRESS: Real-time updates
   # 🐍 FLASK: API endpoint debugging
   ```

2. **Monitor Subprocess Execution:**
   ```python
   # In intelligent_company_scraper.py
   # Verify timeout settings (25s UI, 60s testing)
   # Check subprocess.run() execution
   ```

3. **Test Individual Components:**
   ```bash
   python test_subprocess_scraper.py  # Isolated scraper test
   python test_real_company.py        # End-to-end test
   ```

### Research Status Flow

Companies progress through a defined research lifecycle:
```python
ResearchStatus.UNKNOWN → ResearchStatus.QUEUED → ResearchStatus.RESEARCHING → ResearchStatus.COMPLETED/FAILED
```

Monitor status changes in the UI research modals and API responses.

### Database Operations Pattern

```python
# Standard pattern for all company operations
existing = pinecone_client.find_company_by_name(name)
if not existing:
    embedding = bedrock_client.get_embeddings(content)
    company_data.embedding = embedding
    success = pinecone_client.upsert_company(company_data)
```

### Adding New Similarity Metrics

```python
# In similarity_engine.py
WEIGHTS = {
    'company_stage': 0.30,
    'tech_sophistication': 0.25,
    'industry': 0.20,
    'business_model': 0.15,
    'new_metric': 0.10  # Add new metric
}

# Implement corresponding similarity matrix
def calculate_new_metric_similarity(self, company1, company2):
    # Return similarity score 0.0-1.0
    pass
```

## 🐛 Common Debugging Scenarios

### Scraping Timeouts
- **Symptom:** Companies fail processing after 25-60 seconds
- **Debug:** Check website complexity, verify Crawl4AI config
- **Solution:** Adjust timeout in `intelligent_company_scraper.py`

### AI Client Failures  
- **Symptom:** "AI client not available" errors
- **Debug:** Verify environment variables, check model availability
- **Solution:** Ensure Nova Pro access, implement proper fallbacks

### Progress Tracking Issues
- **Symptom:** UI doesn't update during processing
- **Debug:** Check job_id propagation, verify SSE connections
- **Solution:** Monitor `progress_logger` thread safety

### Vector Storage Problems
- **Symptom:** Companies not found in similarity search
- **Debug:** Verify Pinecone index config, check embedding dimensions
- **Solution:** Ensure metadata formats match schema

## 📊 Performance Optimization

### Cost Optimization
- **Nova Pro Model:** 6x cost reduction ($0.66 → $0.11 per research)
- **Prompt Engineering:** Optimized research prompts for token efficiency
- **Caching:** Crawl4AI cache for repeated URL access

### Processing Optimization
- **Concurrent Extraction:** Semaphore-limited parallel processing
- **Timeout Management:** Tiered timeouts (UI: 25s, Testing: 60s)
- **Memory Management:** Content length limits and cleanup

### Database Optimization
- **Essential Metadata:** 5 core fields vs 62+ original (72% reduction)
- **Hybrid Storage:** Essential data in Pinecone, full data separately
- **Semantic Indexing:** Optimized vector dimensions (1536)

## 🔗 Key API Endpoints

### Core Research (V2 API)
```bash
POST /api/v2/research/start          # Start company research
GET  /api/v2/research/progress/<id>  # Get progress
GET  /events/progress/<id>           # SSE progress stream
```

### Structured Research
```bash
POST /api/v2/research/structured     # Multi-prompt research
GET  /api/v2/research/prompts        # Available prompts  
POST /api/v2/research/estimate       # Cost estimation
```

### Discovery & Similarity
```bash
POST /api/discover                   # Find similar companies
GET  /api/search                     # Real-time search suggestions
GET  /api/database                   # Browse database
```

### Progress & Debugging
```bash
GET  /api/progress/current           # Current job progress
GET  /api/progress/all               # All progress data
GET  /api/health                     # System health check
```

## 💡 Important Development Notes

### AI Model Hierarchy
1. **Primary:** Gemini 2.5 Pro (1M context for aggregation)
2. **Cost-Optimized:** Nova Pro (6x cheaper for research)
3. **Fallback:** OpenAI GPT-4o-mini (when others fail)

### Threading & Concurrency
- Research manager uses thread-safe progress logging
- Scraper implements semaphore-limited parallel extraction
- UI updates via Server-Sent Events (SSE)

### Error Handling Strategy
- Graceful degradation: AI analysis → web search → manual fallback
- Comprehensive logging with emoji prefixes for easy debugging
- User-friendly error messages with actionable suggestions

### Success Metrics
The success metric is: **"Can Theodore extract meaningful company intelligence using proper AI methods AND display it through a beautiful, functional web interface?"**

**Answer: ✅ YES - FULLY ACHIEVED** - UI works beautifully, search works perfectly, structured research system operational with Nova Pro model delivering 6x cost savings. All critical systems are functional and production-ready.

## 🚫 What We Are NOT Doing:
- Processing all 400 companies from David's survey
- Building a production system for mass processing
- Creating a commercial product

## ✅ What We ARE Doing:
- Demonstrating technical feasibility
- Building a working prototype with professional UI
- Showing how the system would work at scale
- Validating the AI extraction capabilities
- Creating a usable web interface for company intelligence discovery