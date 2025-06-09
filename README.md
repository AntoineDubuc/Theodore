# Theodore - AI-Powered Company Intelligence System

🚀 **Transform company research into AI-powered sales intelligence with an intelligent scraping pipeline.**

Theodore provides an advanced company analysis platform with dynamic link discovery, LLM-driven page selection, parallel content extraction, and AI-generated sales intelligence.

## 🎯 Current Features

- **Intelligent Company Scraper**: 4-phase processing with link discovery, LLM page selection, parallel extraction, and AI aggregation
- **Structured Research System**: 8 predefined research prompts with cost transparency and JSON/CSV export
- **Nova Pro AI Model**: 6x cost reduction ($0.66 → $0.11 per research) with enterprise-grade performance
- **Real-time Progress Tracking**: Live phase-by-phase status updates with detailed logging
- **Research Metadata Display**: Shows pages crawled, processing time, and research timestamps in UI
- **Enhanced Sales Intelligence**: AI-generated 2-3 paragraph summaries optimized for sales teams
- **Scrollable Research Modals**: Detailed company information with comprehensive research metadata
- **Modern Web Interface**: Beautiful glass morphism UI with perfect dark mode accessibility at http://localhost:5002
- **Multi-Source Discovery**: Combines Pinecone similarity search with AI-powered recommendations
- **Research Session Management**: Track multi-prompt research operations with comprehensive metrics
- **Smart Database Browser**: View companies with sales intelligence status and one-click website access
- **Universal Website Integration**: Green website buttons throughout the interface for seamless company access
- **WCAG-Compliant Design**: High-contrast dark mode with light blue (#60a5fa) links for optimal readability

## 🏗️ Intelligent Scraper Architecture

```
Company Input → Link Discovery → LLM Page Selection → Parallel Extraction → AI Aggregation → Sales Intelligence
      ↓              ↓                    ↓                    ↓                   ↓                ↓
  Name + URL    robots.txt +       Gemini/Claude         10 Concurrent         Gemini 2.5 Pro    2-3 Paragraph
               sitemaps.xml        Page Analysis          Crawl4AI             Content Fusion     Summary
                +670 links          Select Best           Extractions          (1M tokens)       Optimized
                                   5-10 pages                                                   for Sales
```

## 📊 Current Status

### ✅ Production Ready Features
- **Intelligent Company Processing**: Complete 4-phase scraper with real-time progress tracking
- **Enhanced Sales Intelligence**: AI-generated summaries replacing hardcoded schemas
- **Modern Web Interface**: Beautiful UI with live progress visualization
- **Database Browser**: View and manage companies with sales intelligence status
- **Multi-Model Integration**: Gemini 2.5 Pro + AWS Bedrock Nova Pro + OpenAI working together
- **Vector Storage**: Optimized Pinecone integration with sales intelligence metadata

### ✅ Latest Major Update (December 2025)
- **Structured Research System**: ✅ 8 predefined research prompts covering job listings, decision makers, funding, tech stack, and more
- **Nova Pro Model Integration**: ✅ 6x cost reduction with `amazon.nova-pro-v1:0` for enhanced research operations
- **Research Session Management**: ✅ Track multi-prompt research with cost transparency and export capabilities
- **Enhanced API Endpoints**: ✅ Complete REST API for structured research operations and session management
- **Cost Optimization**: ✅ Real-time cost estimation and tracking for all research operations
- **Export Functionality**: ✅ JSON and CSV export for comprehensive research analysis

### 🎯 Technical Achievements
- **Dynamic Link Discovery**: Automatically discovers 670+ links per company (robots.txt, sitemaps, recursive)
- **LLM Page Selection**: AI chooses most promising 5-10 pages for sales intelligence
- **Parallel Processing**: 10 concurrent Crawl4AI extractions for speed
- **Large Context Processing**: Gemini 2.5 Pro handles 1M+ tokens for content aggregation
- **Production Architecture**: Async processing, error handling, progress tracking, and user feedback

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key
- AWS Bedrock access (optional)
- Pinecone account

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/theodore.git
cd theodore

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

**Web Interface (Recommended)**:
```bash
# Start the web application
python app.py

# Access the modern web interface
# Open: http://localhost:5002
```

### 📊 Complete Research Data Display

Theodore now displays all extracted company intelligence in organized sections:

**Basic Information**:
- Industry, Business Model, Location, Company Size

**Business Details**:
- Target Market, Key Services, Value Proposition, Pain Points

**Technology Information**:
- Tech Stack (development tools, frameworks, platforms)

**Research Metadata**:
- Pages crawled count, Crawl depth, Processing time, Research timestamp

**In Research Details Modal**:
- Complete data across all 13+ fields when available
- Scrollable interface for comprehensive company profiles
- Organized sections for easy information discovery

**For Developers**:
```javascript
// Console logs show detailed research metadata
📋 Pages Crawled: [page1, page2, page3, ...]
📋 Processing Time: 2.5
📋 Research Timestamp: 2024-12-08T18:25:30.123Z
```

**Programmatic Usage**:
```python
from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyIntelligenceConfig

# Initialize Theodore
config = CompanyIntelligenceConfig()
pipeline = TheodoreIntelligencePipeline(config, 
    pinecone_api_key="your-key",
    pinecone_environment="your-env", 
    pinecone_index="theodore-companies")

# Process single company
result = pipeline.process_single_company("Company Name", "https://company.com")
```

## ✨ Key Features

### 📋 Structured Research System

- **8 Predefined Research Prompts**: Job listings, decision makers, products/services, funding, tech stack, news, competitive landscape, customer analysis
- **Cost Transparency**: Real-time cost estimation with Nova Pro pricing ($0.011 per 1K tokens)
- **Research Sessions**: Track multi-prompt research operations with comprehensive metrics
- **Export Capabilities**: JSON and CSV export for analysis and reporting
- **Session Management**: Historical research tracking with success rates and cost analysis

### 🧠 Intelligent Company Scraper

- **Dynamic Link Discovery**: Crawls robots.txt, sitemaps.xml, and recursive page discovery
- **LLM Page Selection**: AI analyzes and selects most promising pages for sales intelligence
- **Parallel Content Extraction**: 10 concurrent Crawl4AI processes for maximum speed
- **AI Content Aggregation**: Gemini 2.5 Pro processes up to 1M tokens for comprehensive summaries

### 🎯 Sales Intelligence Generation

- **AI-Generated Summaries**: 2-3 focused paragraphs optimized for sales teams
- **Dynamic Content**: No hardcoded schemas - LLM decides what's important
- **Business Context**: Includes market positioning, value propositions, and competitive advantages
- **Real-time Progress**: Live 4-phase tracking with detailed logging and status updates

### 📊 Vector Storage & Search

- **Optimized Metadata**: 5 essential fields vs 62+ original (72% cost reduction)
- **Semantic Search**: Find companies by business model, industry, target market
- **Company Clustering**: Automatic sector and similarity grouping
- **Hybrid Storage**: Essential metadata in Pinecone, full data separately

## 📈 Performance Metrics

- **Link Discovery**: 670+ links discovered per company (robots.txt + sitemaps + recursive)
- **Content Quality**: 2-3 paragraph AI summaries vs previous hardcoded 15+ fields
- **Processing Speed**: Parallel extraction with 10 concurrent requests
- **Large Context**: Gemini 2.5 Pro handles 1M+ token aggregation
- **Success Rate**: End-to-end processing with comprehensive error handling

## 🛠️ Technical Stack

- **Intelligent Scraping**: Custom 4-phase pipeline with Crawl4AI integration
- **AI Models**: Gemini 2.5 Pro (1M context), AWS Bedrock Nova Pro, OpenAI GPT-4o-mini
- **Vector Database**: Pinecone serverless with sales intelligence metadata
- **Progress Tracking**: Real-time JSON-based logging with thread-safe updates
- **Web Interface**: Flask + modern CSS/JS with gradient design and live updates

## 📁 Project Structure

```
Theodore/
├── app.py                     # 🌐 Main web application (Flask)
├── src/                       # 🔧 Core application code
│   ├── main_pipeline.py       # Main orchestration
│   ├── models.py              # Pydantic data models  
│   ├── intelligent_company_scraper.py # 🧠 4-phase intelligent scraper
│   ├── intelligent_url_discovery.py  # 🔍 Dynamic link discovery
│   ├── progress_logger.py     # 📊 Real-time progress tracking
│   ├── bedrock_client.py      # AWS AI integration
│   ├── pinecone_client.py     # Optimized vector storage
│   ├── similarity_engine.py   # Enhanced similarity calculations
│   └── similarity_pipeline.py # Similarity processing
├── templates/                 # 🎨 Web UI templates
├── static/                    # 📱 CSS, JavaScript, assets
├── tests/                     # 🧪 Test suite
├── scripts/                   # 🛠️ Utility scripts
├── docs/                      # 📚 Documentation (7 files)
├── config/                    # ⚙️ Configuration management
└── data/                      # 📊 Input data
```

## 📚 Documentation

**Essential Docs**:
- **[Developer Onboarding](docs/DEVELOPER_ONBOARDING.md)**: Complete getting started guide
- **[Setup Guide](docs/setup_guide.md)**: Detailed installation and configuration  
- **[Architecture](docs/architecture.md)**: System design and components

**Technical Deep Dives**:
- **[AI Extraction Pipeline](docs/ai_extraction_pipeline.md)**: Technical implementation details
- **[Vector Storage Strategy](docs/vector_storage_strategy.md)**: Pinecone optimization
- **[Crawl4AI Configuration](docs/crawl4ai_configuration.md)**: Web scraping configuration
- **[Technical Decisions](docs/technical_decisions.md)**: Key decisions and lessons learned

## 🎯 Use Cases

### Business Intelligence
- **Survey Analysis**: Process hundreds of company responses automatically
- **Market Research**: Discover companies by sector, business model, or technology
- **Competitive Analysis**: Find similar companies and analyze market positioning

### Sales & Marketing
- **Lead Qualification**: Automatically research prospect companies
- **Market Segmentation**: Cluster companies by characteristics
- **Opportunity Identification**: Find companies matching ideal customer profiles

### Investment & M&A
- **Deal Sourcing**: Identify potential acquisition targets
- **Market Mapping**: Understand competitive landscapes
- **Due Diligence**: Automated company intelligence gathering

## 🔗 API Endpoints

### Structured Research APIs
```bash
# Get available research prompts
GET /api/research/prompts/available

# Estimate research cost
POST /api/research/prompts/estimate
{
  "selected_prompts": ["job_listings", "decision_makers", "funding_stage"]
}

# Start structured research
POST /api/research/structured/start
{
  "company_name": "OpenAI",
  "website": "https://openai.com",
  "selected_prompts": ["job_listings", "decision_makers"],
  "include_base_research": true
}

# Get research session results
GET /api/research/structured/session/{session_id}

# Export research results
GET /api/research/structured/export/{session_id}?format=csv
```

### Company Discovery APIs
```bash
# Discover similar companies
POST /api/discover
{
  "company_name": "Stripe",
  "max_results": 10
}

# Browse database
GET /api/database/browse?page=1&limit=20

# Get company details
GET /api/company/{company_id}
```

## 💡 Example Queries

```python
# Find AI/ML companies in healthcare
healthcare_ai = pipeline.semantic_search(
    "AI machine learning healthcare medical", 
    filters={"industry": "Healthcare", "business_model": "B2B"}
)

# Discover SaaS startups
saas_startups = pipeline.semantic_search(
    "SaaS software subscription startup",
    filters={"business_model": "SaaS", "company_size": "startup"}
)

# Structured research with cost estimation
from src.research_prompts import research_prompt_library
cost_estimate = research_prompt_library.estimate_total_cost(
    ["job_listings", "decision_makers", "tech_stack"]
)
print(f"Estimated cost: ${cost_estimate['total_cost']:.4f}")
```

## 🔧 Configuration

Theodore supports extensive configuration for different environments:

```python
# Development
config = CompanyIntelligenceConfig(
    max_companies=5,
    enable_caching=True,
    rate_limit_delay=2.0
)

# Production
config = CompanyIntelligenceConfig(
    max_companies=100,
    enable_clustering=True,
    batch_processing=True,
    rate_limit_delay=1.0
)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Crawl4AI**: For providing excellent AI-powered web scraping capabilities
- **OpenAI**: For GPT models that enable intelligent extraction
- **Pinecone**: For scalable vector database infrastructure
- **AWS Bedrock**: For enterprise-grade AI model access

---

**Built for the AI era of business intelligence.** 🚀

*Theodore transforms manual company research into intelligent, automated insights.*