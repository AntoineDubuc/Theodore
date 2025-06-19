# Theodore - Clean Project Structure

## 📁 Current Repository Structure

```
Theodore/
├── 🌐 app.py                        # Main Flask web application
│
├── 📚 docs/                          # Streamlined documentation (8 files)
│   ├── DEVELOPER_ONBOARDING.md      # Complete getting started guide  
│   ├── setup_guide.md               # Installation & configuration
│   ├── architecture.md              # System architecture
│   ├── 🆕 structured_research_guide.md # Structured research system guide
│   ├── ai_extraction_pipeline.md    # AI extraction deep dive
│   ├── vector_storage_strategy.md   # Pinecone optimization
│   ├── crawl4ai_configuration.md    # Web scraping configuration
│   └── technical_decisions.md       # Decisions & lessons learned
│
├── 🔧 src/                          # Core application code
│   ├── main_pipeline.py            # Main orchestration
│   ├── models.py                    # Pydantic data models
│   ├── 🆕 research_prompts.py       # 8 predefined research prompts with cost estimation
│   ├── 🆕 research_manager.py       # Enhanced research manager with session tracking
│   ├── intelligent_company_scraper.py # 🧠 4-phase intelligent scraper
│   ├── intelligent_url_discovery.py  # 🔍 Dynamic link discovery
│   ├── progress_logger.py          # 📊 Real-time progress tracking
│   ├── crawl4ai_scraper.py         # Legacy AI-powered web scraper
│   ├── bedrock_client.py           # AWS AI integration (Nova Pro model)
│   ├── pinecone_client.py          # Optimized vector storage
│   ├── similarity_engine.py        # Enhanced similarity calculations
│   ├── similarity_prompts.py       # AI similarity prompts
│   ├── company_discovery.py        # AI company discovery
│   ├── similarity_pipeline.py      # Similarity processing
│   ├── similarity_validator.py     # Similarity validation
│   └── clustering.py               # Company clustering logic
│
├── 🎨 templates/                    # Web UI templates
│   └── index.html                  # Main web interface
│
├── 📱 static/                       # Web assets
│   ├── css/style.css               # Modern gradient styling
│   ├── js/app.js                   # Frontend JavaScript
│   └── img/favicon.ico             # Site assets
│
├── 🧪 tests/                        # Test suite  
│   ├── test_ai_extraction.py       # AI extraction tests
│   ├── test_single_company.py      # Single company processing
│   ├── test_visterra_query.py      # Query functionality tests
│   ├── test_similarity_engine.py   # Enhanced similarity testing
│   ├── test_claude_direct.py       # Direct Claude testing
│   ├── test_real_ai.py             # Real AI testing
│   └── run_similarity_tests.py     # Similarity testing suite
│
├── 🛠️ scripts/                      # Utility scripts
│   ├── clear_pinecone.py           # Database maintenance
│   ├── extract_raw_pinecone_data.py # Data extraction
│   ├── check_pinecone_database.py  # Database health checks
│   ├── add_test_companies_with_similarity.py # Test data setup
│   ├── test_intelligent_url_discovery.py # URL discovery testing
│   ├── test_similarity_system.py   # Similarity system testing
│   ├── test_with_real_companies.py # Real company testing
│   ├── pinecone_review.py          # Health monitoring
│   └── theodore_cli.py             # CLI interface
│
├── ⚙️ config/                       # Configuration
│   ├── settings.py                 # Application settings
│   └── __init__.py                 # Package initialization
│
├── 📊 data/                         # Input data
│   └── 2025 Survey Respondents Summary May 20.csv
│
├── 📝 logs/                         # Application logs
│
├── 📦 archive/                      # Archived development files
│   ├── README.md                   # Archive documentation
│   ├── development_experiments/    # Research & debugging files
│   ├── old_implementations/        # Superseded code versions
│   ├── debug_scripts/             # One-time analysis scripts
│   └── temp_files/                # Temporary development data
│
├── 🔒 .gitignore                    # Version control exclusions
├── 📋 requirements.txt              # Python dependencies
├── 📖 CLAUDE.md                     # AI development context
└── 📄 PROJECT_STRUCTURE.md          # This file
```

## 🎯 Intelligent Scraper Architecture Benefits

### For New Developers
- **Clear Entry Point**: Start with `docs/DEVELOPER_ONBOARDING.md` for complete setup
- **Modern Web Interface**: Beautiful UI with real-time progress at http://localhost:5001
- **Production Ready**: 4-phase intelligent scraper with sales intelligence generation
- **Comprehensive Testing**: Complete test suite for all major components

### For System Maintenance
- **Modular Scraper**: Intelligent scraper components clearly separated
- **Progress Tracking**: Real-time logging system for debugging and monitoring
- **Enhanced Discovery**: Multi-source similarity discovery with AI recommendations
- **Database Integration**: Optimized Pinecone storage with sales intelligence metadata

### For Future Development
- **Extensible Pipeline**: 4-phase architecture supports easy enhancements
- **Multi-Model Integration**: Gemini, AWS Bedrock, and OpenAI working together
- **Scalable Processing**: Parallel extraction and large context aggregation
- **Sales Intelligence**: AI-generated business summaries optimized for sales teams

## 🧹 Organization Summary

**Latest Updates (June 2025)**:
- **Added Intelligent Scraper**: Complete 4-phase processing system
- **Enhanced Testing**: Comprehensive test suite for new components
- **Improved Scripts**: Additional utility scripts for testing and monitoring
- **Documentation Updated**: README and onboarding guide reflect current architecture
- **Repository Cleanup**: Removed temporary files and test artifacts

**Current Architecture**:
- **Intelligent Company Scraper**: Dynamic link discovery, LLM page selection, parallel extraction, AI aggregation
- **Real-time Progress Tracking**: Thread-safe JSON logging with live UI updates
- **Sales Intelligence Generation**: AI-generated 2-3 paragraph business summaries
- **Enhanced Discovery**: Multi-source similarity search with AI recommendations
- **Production Ready**: End-to-end functionality with comprehensive error handling

## 🚀 Production-Ready Components

### Core Production Files
```python
src/
├── models.py                        # ✅ Pydantic models with validation
├── intelligent_company_scraper.py   # ✅ 4-phase intelligent processing
├── intelligent_url_discovery.py    # ✅ Dynamic link discovery system
├── progress_logger.py              # ✅ Real-time progress tracking
├── similarity_engine.py            # ✅ Enhanced similarity calculations
├── pinecone_client.py              # ✅ Sales intelligence metadata storage
├── bedrock_client.py               # ✅ AWS AI integration
└── main_pipeline.py                # ✅ Complete orchestration pipeline
```

### Key Technical Achievements
1. **Intelligent Scraper Architecture**: Complete 4-phase processing with dynamic content discovery
2. **Large Context Processing**: Gemini 2.5 Pro handling 1M+ tokens for content aggregation
3. **Parallel Processing**: 10 concurrent Crawl4AI extractions for maximum speed
4. **Real-time Progress Tracking**: Thread-safe JSON logging with live UI updates
5. **Sales Intelligence Generation**: AI-generated business summaries optimized for sales teams
6. **Multi-Source Discovery**: Enhanced similarity search combining Pinecone + AI recommendations

### Quality Assurance
- ✅ **Comprehensive Documentation**: Updated guides reflecting intelligent scraper architecture
- ✅ **Enhanced Test Suite**: Testing for intelligent scraper and similarity components
- ✅ **Production Utilities**: Database maintenance, testing, and monitoring scripts
- ✅ **Real-time Monitoring**: Progress tracking and error handling systems
- ✅ **Clean Repository**: Organized structure with archived development history

## 📈 Business Impact

**Before Cleanup**:
- 46 Python files scattered across repository
- Mixed development experiments with production code
- Difficult for new developers to understand current state
- No clear documentation of technical decisions

**After Cleanup**:
- 11 production Python files in logical structure
- Complete development history preserved in archive
- Clear onboarding path for new developers
- Comprehensive documentation of architecture and decisions

**ROI**: Significantly improved developer productivity and reduced onboarding time while preserving valuable development context.

## 🔮 Future Maintenance

### Regular Tasks
1. **Update Documentation**: Keep docs current with code changes
2. **Archive Management**: Move obsolete files to appropriate archive categories
3. **Test Maintenance**: Update tests for new features and bug fixes
4. **Dependency Updates**: Keep requirements.txt current and secure

### Growth Considerations
- **Microservices**: Current structure supports service decomposition
- **API Addition**: Clear place for REST API controllers
- **Multi-Tenant**: Configuration structure supports tenant isolation
- **Monitoring**: Logging and metrics infrastructure in place

---

*This clean, production-focused structure maintains Theodore's complete development context while providing an excellent foundation for future growth and new team member onboarding.*