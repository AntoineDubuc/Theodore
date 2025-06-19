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

# Start V2 application (enhanced interface with advanced features - experimental)
python3 src/experimental/v2_app.py &
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

# Additional test files in organized test directories
python tests/sandbox/testing_sandbox/test_v2_research.py
python tests/sandbox/testing_sandbox/test_v2_discovery.py
python tests/sandbox/testing_sandbox/minimal_test.py

# Legacy tests (reference only)
python tests/legacy/test_similarity_pipeline.py

# Note: Test files have been reorganized into tests/ with subdirectories:
# tests/legacy/ - Legacy test implementations
# tests/sandbox/ - Development and experimental tests
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

## 📁 Project Organization

### Clean Codebase Structure

Theodore has been reorganized for maintainability and clarity:

**Production Code (Core System):**
```
src/
├── main_pipeline.py                   # Core orchestration
├── models.py                          # Pydantic data models
├── intelligent_company_scraper.py     # 4-phase scraper (primary)
├── simple_enhanced_discovery.py       # Similarity discovery (primary)
├── bedrock_client.py                  # AWS AI integration
├── gemini_client.py                   # Google AI integration
├── openai_client.py                   # OpenAI fallback
├── pinecone_client.py                 # Vector database
└── progress_logger.py                 # Real-time progress tracking
```

**Organized Development Resources:**
```
src/
├── experimental/                      # Experimental features and research
├── legacy/                           # Legacy implementations (reference)
│   ├── research_manager.py          # Structured research prompts
│   └── similarity_prompts.py        # Research prompt definitions
└── sheets_integration/               # Google Sheets batch processing

tests/
├── legacy/                           # Legacy test implementations
└── sandbox/                          # Development and experimental tests

docs/
├── core/                             # Essential documentation
├── technical/                        # Component-specific docs
├── features/                         # Feature documentation
├── outdated/                         # Pre-reorganization reference
└── legacy/                           # Historical documentation
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
│  1. Comprehensive Link Discovery (robots.txt + sitemap +   │
│     recursive crawling) → 2. LLM-Driven Page Selection     │
│     (targets /contact, /about, /team, /careers) →          │
│  3. Parallel Content Extraction (up to 50 pages) →        │
│  4. LLM Content Aggregation (1M token context)            │
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

**Core Pipeline (Production):**
- `src/main_pipeline.py` - Main orchestration and entry point
- `src/models.py` - Pydantic data models for all entities
- `src/intelligent_company_scraper.py` - 4-phase intelligent scraping system
- `src/simple_enhanced_discovery.py` - Similarity discovery engine (primary)
- `src/progress_logger.py` - Thread-safe real-time progress tracking

**Legacy Components (Reference Only):**
- `src/legacy/research_manager.py` - Structured research with 8 predefined prompts
- `src/legacy/similarity_prompts.py` - Research prompt definitions
- `src/experimental/similarity_engine.py` - Multi-dimensional similarity scoring

### Intelligent Scraping System (intelligent_company_scraper.py)

The core of Theodore's data extraction uses a sophisticated 4-phase approach that combines comprehensive web crawling with AI-driven analysis:

#### **Phase 1: Comprehensive Link Discovery**
```python
# Discovers up to 1000 links from multiple sources:
1. robots.txt parsing - Additional paths and sitemaps
2. sitemap.xml analysis - Structured site navigation
3. Recursive crawling - 3 levels deep with max_depth=3
4. Link filtering - Removes noise and invalid URLs
```

**What it discovers:**
- All major site sections (`/about`, `/contact`, `/careers`, `/team`)
- Product/service pages (`/products`, `/services`, `/solutions`)
- Corporate pages (`/leadership`, `/investors`, `/news`)
- Support pages (`/security`, `/compliance`, `/partners`)

#### **Phase 2: LLM-Driven Page Selection**
The system uses a specialized prompt to intelligently select the most valuable pages:

```python
# LLM analyzes all discovered links and prioritizes based on:
- Contact & Location data (contact pages, about pages)
- Company founding information (history, our-story sections)  
- Employee count indicators (team, careers, about pages)
- Leadership information (team, management pages)
- Business intelligence (products, services, competitive info)

# Selects up to 50 most promising pages for data extraction
```

**Target page patterns:**
- `/contact*` or `/get-in-touch*` → Contact info + location
- `/about*` or `/company*` → Founding year + company size  
- `/team*` or `/leadership*` → Decision makers and executives
- `/careers*` or `/jobs*` → Employee count + company culture
- Footer pages → Social media links and legal information

#### **Phase 3: Parallel Content Extraction**
```python
# High-performance content extraction:
- Concurrent processing: 10 pages simultaneously
- Content optimization: Removes nav, footer, scripts, styles
- Targeted selectors: main, article, .content, .main-content
- Content limits: 10,000 characters per page maximum
- Real-time progress: Live updates during extraction
```

**Technical approach:**
- Uses Crawl4AI with Chromium browser for JavaScript execution
- Clean text extraction with structured content filtering
- Respects robots.txt and implements proper crawling etiquette
- Caches results to avoid repeated requests

#### **Phase 4: LLM Content Aggregation**
```python
# Comprehensive analysis using Gemini 2.5 Pro:
- Combines content from all scraped pages (up to 5,000 chars each)
- 1M token context window for complete site analysis
- Generates structured business intelligence summary
- Focuses on sales-relevant information and company insights
```

**Analysis output:**
- Company overview and value proposition
- Business model and revenue approach  
- Target market and customer segments
- Products/services and competitive advantages
- Company maturity and sales context

### Current Extraction Performance

**Successfully extracts (high success rate):**
- Company descriptions and value propositions
- Business models (B2B/B2C classification)
- Industry and market segments
- Technical sophistication assessments
- Company size and stage indicators

**Consistently challenging (improvement needed):**
- Founding years (often in timeline graphics)
- Physical locations (complex footer/contact parsing)
- Employee counts (typically not published)
- Contact details (behind forms, not plain text)
- Social media links (complex footer structures)
- Leadership teams (separate page navigation)

### Improvement Areas Identified

The scraping system is highly sophisticated and DOES crawl comprehensive content from targeted pages. Current limitations are primarily in:

1. **LLM Prompt Focus**: Current aggregation prompt emphasizes narrative summaries over structured data extraction
2. **Content Processing**: Some key data (contact info, dates) requires specialized parsing beyond general text extraction  
3. **Multi-page Coordination**: Founding dates and leadership info may span multiple related pages
4. **Structured Data**: Could benefit from JSON-LD and microdata parsing for contact/location info

**AI Integration:**
- `src/bedrock_client.py` - AWS Bedrock integration (Nova Pro model)
- `src/gemini_client.py` - Google Gemini integration (primary analysis)
- `src/openai_client.py` - OpenAI integration (fallback)

**Data & Storage:**
- `src/pinecone_client.py` - Vector database operations
- `src/progress_logger.py` - Thread-safe real-time progress tracking

**Web Interface:**
- `app.py` - Flask application with comprehensive API endpoints (primary interface)
- `templates/index.html` - Modern dark-themed UI (primary)
- `templates/settings.html` - Configuration and settings UI
- `static/js/app.js` - Frontend logic with real-time updates
- `static/css/style.css` - Modern gradient styling with dark theme

**Experimental/Development:**
- `src/experimental/v2_app.py` - V2 Flask application with enhanced research features
- `templates/v2_index.html` - Enhanced V2 UI
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

### Import Patterns After Reorganization

**Core imports (production code):**
```python
# Main pipeline and models
from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyData, CompanyIntelligenceConfig
from src.intelligent_company_scraper import IntelligentCompanyScraperSync
from src.simple_enhanced_discovery import SimpleEnhancedDiscovery

# AI clients
from src.bedrock_client import BedrockClient
from src.gemini_client import GeminiClient
from src.pinecone_client import PineconeClient
```

**Legacy/experimental imports:**
```python
# Legacy research system (reference only)
from src.legacy.research_manager import ResearchManager
from src.legacy.similarity_prompts import INDUSTRY_CLASSIFICATION_FROM_RESEARCH_PROMPT

# Experimental features
from src.experimental.v2_research import V2ResearchManager
from src.experimental.similarity_engine import SimilarityEngine
```

### Adding New Research Prompts (Legacy System)

```python
# In src/legacy/research_prompts.py
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

1. **Monitor 4-Phase Execution:**
   ```python
   # Watch for these phase-specific logs:
   # 🔍 LINK DISCOVERY: robots.txt, sitemap, recursive crawling
   # 🎯 PAGE SELECTION: LLM analyzing links for best targets
   # 📄 CONTENT EXTRACTION: Parallel page scraping progress
   # 🧠 AI AGGREGATION: LLM combining all content into intelligence
   ```

2. **Debug Page Selection Issues:**
   ```python
   # Check if LLM is selecting appropriate pages:
   # Look for: /contact, /about, /team, /careers in selected URLs
   # Verify: 10-50 pages selected from discovered links
   # Monitor: LLM page selection vs heuristic fallback
   ```

3. **Content Extraction Monitoring:**
   ```python
   # Real-time extraction feedback:
   # 🔍 [1/20] Starting: https://company.com/about
   # ✅ [1/20] Success: https://company.com/about  
   # 📄 Content preview: Company founded in 1995...
   # ❌ [2/20] Failed: https://company.com/contact - No content
   ```

4. **LLM Analysis Verification:**
   ```python
   # Check aggregation quality:
   # Gemini 2.5 Pro with 1M context processes all page content
   # Content from 5-50 pages combined into business intelligence
   # Look for structured summaries vs generic marketing copy
   ```

5. **Test Individual Components:**
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
- **Concurrent Page Crawling:** 10-page parallel extraction with semaphore limiting (10x per-page improvement)
- **Performance Results:** 15 pages extracted in 5.2 seconds (vs 35+ seconds sequential)
- **Thread-Safe LLM Processing:** 2-worker concurrent pool with ThreadLocalGeminiClient
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

### Technical Capabilities Demonstrated

#### **Sophisticated Web Crawling:**
- ✅ **Multi-source link discovery**: robots.txt + sitemap.xml + recursive crawling (up to 1000 links)
- ✅ **AI-driven page selection**: LLM intelligently chooses 10-50 most valuable pages from all discovered links
- ✅ **Parallel content extraction**: Concurrent processing of selected pages with real-time progress
- ✅ **Comprehensive content analysis**: Gemini 2.5 Pro with 1M token context processes all page content

#### **Advanced Data Processing:**
- ✅ **4-phase intelligent pipeline**: Link discovery → LLM selection → parallel extraction → AI aggregation  
- ✅ **Targeted page identification**: Specifically seeks /contact, /about, /team, /careers for missing data
- ✅ **Clean content extraction**: Removes navigation, footer, scripts while preserving main content
- ✅ **Business intelligence generation**: Converts raw web content into structured company insights

#### **Production-Ready Architecture:**
- ✅ **Cost-optimized AI models**: 6x reduction with Nova Pro ($0.66 → $0.11 per research)
- ✅ **Real-time progress tracking**: Live updates during 4-phase extraction process
- ✅ **Error handling & fallbacks**: Graceful degradation when LLM or scraping fails
- ✅ **Scalable processing**: Handles complex websites with JavaScript and dynamic content

#### **Current Performance:**
- **Processing Speed**: 20-35 seconds total per company (vs 47+ seconds previously)
- **Concurrent Extraction**: 15 pages processed in 5.2 seconds (10x per-page improvement)
- **Data extraction success**: 18+ structured fields per company (vs 3-5 with basic scraping)
- **Content comprehensiveness**: Analyzes 5-50 pages per company with full text analysis
- **Business intelligence quality**: Generates sales-ready company summaries with market context
- **Technical sophistication**: Successfully processes modern websites with complex architectures

The system demonstrates that Theodore can indeed extract meaningful company intelligence using sophisticated AI methods, far beyond simple web scraping approaches.

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

## 📚 Documentation Structure

The project documentation is well-organized for different audiences:

**For New Developers:**
- Start with `docs/core/DEVELOPER_ONBOARDING_NEW.md` for complete setup
- Review `docs/core/CORE_ARCHITECTURE.md` for system understanding
- Check `docs/core/setup_guide.md` for installation details

**For Technical Implementation:**
- `docs/technical/` contains component-specific documentation
- `docs/features/` covers experimental features and batch processing
- `docs/outdated/` and `docs/legacy/` provide historical reference

**Documentation Status:**
- ✅ **Core docs**: Current and maintained
- ⚠️ **Technical docs**: May need updates, verify before use
- 🔬 **Feature docs**: Experimental/partial implementations
- 📚 **Legacy/Outdated**: Historical reference only