# Theodore - AI-Powered Company Intelligence System

🚀 **Transform company research into AI-powered sales intelligence with an intelligent scraping pipeline.**

Theodore provides an advanced company analysis platform with dynamic link discovery, LLM-driven page selection, parallel content extraction, and AI-generated sales intelligence.

## 🎯 Current Features

- **Intelligent Company Scraper**: 4-phase processing with link discovery, LLM page selection, parallel extraction, and AI aggregation
- **Real-time Progress Tracking**: Live phase-by-phase status updates with detailed logging
- **Enhanced Sales Intelligence**: AI-generated 2-3 paragraph summaries optimized for sales teams
- **Modern Web Interface**: Beautiful gradient-styled UI with progress visualization at http://localhost:5001
- **Multi-Source Discovery**: Combines Pinecone similarity search with AI-powered recommendations
- **Smart Database Browser**: View companies with sales intelligence status and metadata

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
- **Multi-Model Integration**: Gemini 2.5 Pro + AWS Bedrock + OpenAI working together
- **Vector Storage**: Optimized Pinecone integration with sales intelligence metadata

### ✅ Latest Major Update (June 2025)
- **Intelligent Scraper**: ✅ Complete overhaul from hardcoded extraction to dynamic LLM-driven processing
- **Real-time Progress**: ✅ Live 4-phase tracking with detailed logging and UI updates
- **Enhanced Discovery**: ✅ Multi-source similarity discovery (Pinecone + AI recommendations)
- **Sales Intelligence**: ✅ AI-generated 2-3 paragraph summaries optimized for sales teams
- **UI Integration**: ✅ Fixed database browser, progress tracking, and result display

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
# Open: http://localhost:5001
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
- **AI Models**: Gemini 2.5 Pro (1M context), AWS Bedrock Claude Sonnet 4, OpenAI GPT-4o-mini
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

# Find companies with specific technology
tech_companies = pipeline.semantic_search(
    "Python React AWS cloud infrastructure",
    top_k=10
)
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