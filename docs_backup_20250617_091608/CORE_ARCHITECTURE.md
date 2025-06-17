# 🏗️ Theodore Core Architecture

This document outlines the **clean, functional architecture** of Theodore after the codebase reorganization.

## 🎯 Overview

Theodore is a **production-ready AI company intelligence system** with a 4-layer architecture:

1. **Web Interface Layer** - Flask + HTML/CSS/JS
2. **API Layer** - RESTful endpoints with real-time progress
3. **Core Business Logic** - 4-phase scraping + similarity discovery
4. **External Services** - AI models + vector database + web scraping

## 📁 Core File Structure

### Production Files (Core System)
```
Theodore/
├── app.py                                  # 🌐 Main Flask application
├── templates/
│   ├── index.html                         # 🎨 Primary UI (4 tabs)
│   └── settings.html                      # ⚙️ Configuration UI
├── static/
│   ├── css/style.css                      # 💄 Styling
│   └── js/app.js                          # 🧠 Frontend logic
└── src/
    ├── main_pipeline.py                   # 🔧 Core orchestration
    ├── models.py                          # 📋 Pydantic data models
    ├── intelligent_company_scraper.py     # 🕷️ 4-phase scraper
    ├── simple_enhanced_discovery.py       # 🔍 Similarity engine
    ├── bedrock_client.py                  # 🤖 AWS AI client
    ├── pinecone_client.py                 # 🗃️ Vector database
    ├── gemini_client.py                   # 🧮 Google AI client
    ├── openai_client.py                   # 🔄 OpenAI fallback
    └── progress_logger.py                 # 📊 Real-time progress
```

### Organized Resources (Reference/Development)
```
├── src/experimental/                      # 🔬 Experimental features
├── src/legacy/                           # 📚 Legacy implementations  
├── tests/                                # 🧪 Test files
├── scripts/                              # 🛠️ Utility scripts
├── docs/                                 # 📖 Documentation
└── config/                               # ⚙️ Configuration
```

## 🌊 Data Flow Architecture

### 1. Company Discovery Flow
```
User Input (Company Name)
    ↓
Frontend: handleDiscovery() [app.js]
    ↓
API: POST /api/discover [app.py]
    ↓
Business Logic: SimpleEnhancedDiscovery [simple_enhanced_discovery.py]
    ↓
AI Analysis: Bedrock/Gemini clients
    ↓
Vector Search: Pinecone similarity search
    ↓
Results: JSON response → UI display
```

### 2. Company Processing Flow
```
User Input (Company + Website)
    ↓
Frontend: handleProcessing() [app.js]
    ↓
API: POST /api/process-company [app.py]
    ↓
Core Logic: IntelligentCompanyScraperSync [intelligent_company_scraper.py]
    ↓
4-Phase Processing:
├── Phase 1: Link Discovery (robots.txt, sitemaps, crawling)
├── Phase 2: LLM Page Selection (AI chooses best pages)
├── Phase 3: Parallel Extraction (concurrent scraping)
└── Phase 4: AI Aggregation (content synthesis)
    ↓
Storage: Pinecone vector storage with embeddings
    ↓
Progress Updates: Real-time UI feedback via progress_logger
    ↓
Results: Success response → UI display
```

### 3. Database Management Flow
```
User Action (Refresh/Clear/Add)
    ↓
Frontend: Database functions [app.js]
    ↓
API: Various /api/database/* endpoints [app.py]
    ↓
Database Logic: PineconeClient [pinecone_client.py]
    ↓
Operations: Query/Insert/Delete vectors
    ↓
Results: Company list → UI table display
```

## 🧩 Component Architecture

### Frontend Components

#### 1. Main UI (templates/index.html)
- **4 Tabs**: Discovery, Process, Database, Batch
- **Real-time updates**: Progress bars, live logs
- **Responsive design**: Mobile-friendly interface
- **Error handling**: User-friendly error messages

#### 2. JavaScript Logic (static/js/app.js)
- **Event handlers**: Form submissions, button clicks
- **API communication**: Fetch requests to backend
- **Progress tracking**: Real-time progress updates
- **UI management**: Tab switching, modal dialogs

### Backend Components

#### 1. Flask Application (app.py)
- **API routes**: RESTful endpoints for all features
- **Error handling**: Comprehensive error responses
- **Pipeline integration**: Coordinates all backend services
- **Real-time communication**: Server-sent events for progress

#### 2. Core Pipeline (src/main_pipeline.py)
- **Service orchestration**: Coordinates AI clients and database
- **Configuration management**: Loads settings and credentials
- **Component initialization**: Sets up all backend services

#### 3. Intelligent Scraper (src/intelligent_company_scraper.py)
**4-Phase Processing System:**
- **Phase 1 - Link Discovery**: 
  - robots.txt parsing
  - sitemap.xml analysis  
  - Recursive crawling (3 levels)
  - Up to 1000 links discovered
- **Phase 2 - LLM Page Selection**:
  - AI analyzes all discovered links
  - Prioritizes by data value (contact, about, team, careers)
  - Selects 10-50 most promising pages
- **Phase 3 - Parallel Extraction**:
  - Concurrent processing (10 pages simultaneously)
  - Clean content extraction
  - Progress tracking
- **Phase 4 - AI Aggregation**:
  - Gemini 2.5 Pro content synthesis
  - 1M token context window
  - Business intelligence generation

#### 4. Discovery Engine (src/simple_enhanced_discovery.py)
- **Similarity calculation**: Multi-dimensional company matching
- **Vector search**: Pinecone semantic search
- **AI enhancement**: Smart result ranking and filtering
- **Real-time processing**: Fast response times

### AI Client Architecture

#### 1. AWS Bedrock Client (src/bedrock_client.py)
- **Primary role**: Cost-optimized embeddings and analysis
- **Model**: amazon.nova-pro-v1:0 (6x cost reduction)
- **Features**: Embedding generation, text analysis

#### 2. Gemini Client (src/gemini_client.py)  
- **Primary role**: Large context analysis and aggregation
- **Model**: Gemini 2.5 Pro (1M token context)
- **Features**: Content synthesis, complex reasoning

#### 3. OpenAI Client (src/openai_client.py)
- **Primary role**: Fallback for when other services fail
- **Model**: GPT-4o-mini
- **Features**: Reliable backup processing

## 🔌 External Service Integration

### 1. Pinecone Vector Database
- **Purpose**: Store company embeddings and metadata
- **Operations**: Upsert, query, delete vectors
- **Optimization**: Essential metadata only (72% storage reduction)

### 2. Crawl4AI Web Scraping
- **Purpose**: High-performance web content extraction
- **Features**: JavaScript execution, content cleaning, caching
- **Integration**: Used within intelligent scraper phases

### 3. AI Service APIs
- **AWS Bedrock**: Primary AI processing
- **Google Gemini**: Large context analysis
- **OpenAI**: Fallback processing

## 🎛️ Configuration Architecture

### 1. Settings Management (config/settings.py)
- **Pydantic-based**: Type-safe configuration
- **Environment variables**: Automatic loading from .env
- **Validation**: Built-in validation and error handling

### 2. Credentials Management
- **Service accounts**: Google Cloud credentials
- **API keys**: AWS, Pinecone, AI services
- **Security**: Environment-based, not hardcoded

## 📊 Progress & Monitoring

### 1. Real-time Progress (src/progress_logger.py)
- **Thread-safe**: Concurrent progress updates
- **Granular tracking**: Phase-by-phase progress
- **UI integration**: Live updates in frontend

### 2. Error Handling
- **Graceful degradation**: Fallback mechanisms
- **User-friendly messages**: Clear error communication
- **Comprehensive logging**: Debug-friendly logs

## 🚀 Performance Architecture

### 1. Concurrent Processing
- **Parallel scraping**: 10 simultaneous page extractions
- **Async operations**: Non-blocking AI calls
- **Timeout management**: Configurable timeouts

### 2. Caching Strategy
- **Crawl4AI caching**: Automatic content caching
- **Vector caching**: Embedding reuse
- **Database optimization**: Efficient Pinecone queries

### 3. Cost Optimization
- **Model selection**: Cost-effective AI model choices
- **Token optimization**: Efficient prompt engineering
- **Resource management**: Careful API usage

## 🔒 Security Architecture

### 1. API Security
- **Environment variables**: Secure credential storage
- **Input validation**: Pydantic model validation
- **Error sanitization**: No sensitive data in responses

### 2. Data Privacy
- **No persistent storage**: Only vector embeddings stored
- **Minimal metadata**: Essential data only
- **Secure transmission**: HTTPS for all API calls

## 🎯 Architectural Principles

### 1. Separation of Concerns
- **Frontend**: Pure UI logic, no business logic
- **API Layer**: HTTP handling, no complex processing
- **Business Logic**: Core processing, reusable components
- **External Services**: Isolated service integrations

### 2. Modularity
- **Independent components**: Each module has clear responsibility
- **Loose coupling**: Minimal dependencies between components
- **Easy testing**: Isolated units for testing

### 3. Scalability
- **Horizontal scaling**: Stateless design
- **Resource efficiency**: Optimized processing
- **Performance monitoring**: Built-in progress tracking

### 4. Maintainability
- **Clean code**: Self-documenting, minimal comments
- **Consistent patterns**: Standardized approaches
- **Documentation**: Clear architectural documentation

## 🔮 Extension Points

### 1. Adding New Features
- **Frontend**: Extend UI tabs and JavaScript handlers
- **Backend**: Add new API routes and business logic
- **Integration**: Connect to new external services

### 2. AI Model Integration
- **Client pattern**: Follow existing AI client structure
- **Fallback chain**: Add to existing fallback mechanism
- **Configuration**: Add to settings management

### 3. Data Processing
- **Pipeline extension**: Add new processing phases
- **Model enhancement**: Extend Pydantic models
- **Storage optimization**: Enhance Pinecone integration

---

This architecture provides a **solid foundation** for Theodore's continued development while maintaining clean separation of concerns and excellent performance characteristics.