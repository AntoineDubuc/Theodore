# 🔄 Theodore Company Data Retrieval - Mermaid Diagrams

High-contrast Mermaid diagrams documenting Theodore's company data retrieval process.

## 📊 Complete System Architecture

```mermaid
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#ff6b6b',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#ff4757',
    'lineColor': '#ffa502',
    'secondaryColor': '#2ed573',
    'tertiaryColor': '#5352ed',
    'background': '#2f3542',
    'mainBkg': '#2f3542',
    'secondBkg': '#57606f',
    'tertiaryBkg': '#3742fa'
  }
}}%%

graph TB
    %% User Interface Layer
    subgraph UI["🎨 USER INTERFACE LAYER"]
        DiscoveryTab["🔍 Discovery Tab<br/>Find Similar Companies"]
        ProcessTab["⚙️ Process Tab<br/>Add New Company"]
        DatabaseTab["🗃️ Database Tab<br/>Browse All Companies"]
        SettingsTab["⚙️ Settings Tab<br/>Configuration"]
    end
    
    %% API Layer
    subgraph API["🔗 FLASK API ENDPOINTS"]
        DiscoverAPI["/api/discover<br/>POST"]
        ProcessAPI["/api/process-company<br/>POST"]
        DatabaseAPI["/api/database<br/>GET"]
        SettingsAPI["/api/settings<br/>GET/POST"]
    end
    
    %% Core Processing
    subgraph CORE["🧠 CORE PROCESSING ENGINE"]
        SimpleDiscovery["SimpleEnhancedDiscovery<br/>🔍 AI + Vector Search"]
        IntelligentScraper["IntelligentCompanyScraper<br/>🕷️ 4-Phase Pipeline"]
        MainPipeline["TheodoreIntelligencePipeline<br/>🔧 Orchestration"]
    end
    
    %% AI Services
    subgraph AI["🤖 AI MODEL SERVICES"]
        Gemini["Gemini 2.5 Pro<br/>📝 Content Aggregation<br/>1M Token Context"]
        Bedrock["AWS Bedrock<br/>🧮 Nova Pro Model<br/>6x Cost Reduction"]
        OpenAI["OpenAI GPT-4o-mini<br/>🔄 Fallback Service"]
    end
    
    %% Storage
    subgraph STORAGE["🗃️ VECTOR DATABASE"]
        Pinecone["Pinecone<br/>📊 Vector Storage<br/>1536 Dimensions"]
        Metadata["Essential Metadata<br/>📋 5 Core Fields<br/>72% Reduction"]
    end
    
    %% Data Flow Connections
    DiscoveryTab --> DiscoverAPI
    ProcessTab --> ProcessAPI
    DatabaseTab --> DatabaseAPI
    SettingsTab --> SettingsAPI
    
    DiscoverAPI --> SimpleDiscovery
    ProcessAPI --> MainPipeline
    DatabaseAPI --> Pinecone
    
    SimpleDiscovery --> Pinecone
    SimpleDiscovery --> Bedrock
    
    MainPipeline --> IntelligentScraper
    IntelligentScraper --> Gemini
    MainPipeline --> Bedrock
    
    Bedrock --> Pinecone
    Gemini --> Pinecone
    Pinecone --> Metadata
    
    %% Styling
    classDef uiStyle fill:#ff6b6b,stroke:#ff4757,stroke-width:3px,color:#ffffff
    classDef apiStyle fill:#ffa502,stroke:#ff6348,stroke-width:3px,color:#ffffff
    classDef coreStyle fill:#2ed573,stroke:#20bf6b,stroke-width:3px,color:#ffffff
    classDef aiStyle fill:#5352ed,stroke:#3742fa,stroke-width:3px,color:#ffffff
    classDef storageStyle fill:#8e44ad,stroke:#9b59b6,stroke-width:3px,color:#ffffff
    
    class DiscoveryTab,ProcessTab,DatabaseTab,SettingsTab uiStyle
    class DiscoverAPI,ProcessAPI,DatabaseAPI,SettingsAPI apiStyle
    class SimpleDiscovery,IntelligentScraper,MainPipeline coreStyle
    class Gemini,Bedrock,OpenAI aiStyle
    class Pinecone,Metadata storageStyle
```

## 🔄 4-Phase Intelligent Scraping Pipeline

```mermaid
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#ff6b6b',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#ff4757',
    'lineColor': '#ffa502',
    'secondaryColor': '#2ed573',
    'tertiaryColor': '#5352ed',
    'background': '#2f3542',
    'mainBkg': '#2f3542',
    'secondBkg': '#57606f'
  }
}}%%

flowchart TD
    Start["🚀 Company Input<br/>Name + Website URL"] --> Phase1
    
    subgraph Phase1["🔍 PHASE 1: LINK DISCOVERY"]
        RobotsTxt["🤖 robots.txt<br/>Parse additional paths<br/>Find sitemaps"]
        Sitemap["🗺️ sitemap.xml<br/>Structured navigation<br/>All site sections"]
        Recursive["🔄 Recursive Crawling<br/>3 levels deep<br/>Navigation links"]
        
        RobotsTxt --> Combine1["📝 Combine Links<br/>Up to 1000 URLs"]
        Sitemap --> Combine1
        Recursive --> Combine1
    end
    
    Phase1 --> Phase2
    
    subgraph Phase2["🎯 PHASE 2: LLM PAGE SELECTION"]
        LLMAnalysis["🧠 Gemini 2.5 Flash<br/>Analyze all discovered links<br/>Intelligent prioritization"]
        Selection["✅ Select 10-50 Pages<br/>• /contact, /about<br/>• /team, /careers<br/>• /products, /services<br/>• Business intelligence"]
        
        LLMAnalysis --> Selection
    end
    
    Phase2 --> Phase3
    
    subgraph Phase3["📄 PHASE 3: PARALLEL EXTRACTION"]
        Crawl4AI["🕷️ Crawl4AI AsyncWebCrawler<br/>Chromium browser<br/>JavaScript execution"]
        Parallel["⚡ 10 Concurrent Requests<br/>Real-time progress<br/>Content optimization"]
        Clean["🧹 Clean Content<br/>Remove nav/footer<br/>Preserve main content"]
        
        Crawl4AI --> Parallel
        Parallel --> Clean
    end
    
    Phase3 --> Phase4
    
    subgraph Phase4["🧠 PHASE 4: AI AGGREGATION"]
        Aggregate["🔮 Gemini 2.5 Pro<br/>1M token context<br/>Process all page content"]
        Intelligence["📊 Sales Intelligence<br/>2-3 paragraph summary<br/>Business context<br/>Market positioning"]
        
        Aggregate --> Intelligence
    end
    
    Phase4 --> Storage
    
    subgraph Storage["🗃️ STORAGE & ANALYSIS"]
        Analysis["🤖 Bedrock Analysis<br/>Industry classification<br/>Business model<br/>Company stage"]
        Embedding["📐 Vector Embedding<br/>Amazon Titan<br/>1536 dimensions"]
        Database["🗄️ Pinecone Storage<br/>Vector + metadata<br/>Semantic search ready"]
        
        Analysis --> Embedding
        Embedding --> Database
    end
    
    %% Progress tracking
    Phase1 -.-> Progress["📊 Real-time Progress<br/>Live UI updates<br/>Phase-by-phase status"]
    Phase2 -.-> Progress
    Phase3 -.-> Progress
    Phase4 -.-> Progress
    
    %% Styling
    classDef phaseStyle fill:#ff6b6b,stroke:#ff4757,stroke-width:3px,color:#ffffff
    classDef processStyle fill:#2ed573,stroke:#20bf6b,stroke-width:2px,color:#ffffff
    classDef aiStyle fill:#5352ed,stroke:#3742fa,stroke-width:2px,color:#ffffff
    classDef storageStyle fill:#8e44ad,stroke:#9b59b6,stroke-width:2px,color:#ffffff
    classDef progressStyle fill:#ffa502,stroke:#ff6348,stroke-width:2px,color:#ffffff
    
    class Start phaseStyle
    class RobotsTxt,Sitemap,Recursive,Combine1,LLMAnalysis,Selection,Crawl4AI,Parallel,Clean processStyle
    class Aggregate,Intelligence,Analysis aiStyle
    class Embedding,Database storageStyle
    class Progress progressStyle
```

## 🔍 Company Discovery Workflow

```mermaid
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#ff6b6b',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#ff4757',
    'lineColor': '#ffa502',
    'secondaryColor': '#2ed573',
    'tertiaryColor': '#5352ed',
    'background': '#2f3542',
    'mainBkg': '#2f3542',
    'secondBkg': '#57606f'
  }
}}%%

flowchart TD
    UserInput["👤 User Input<br/>Company Name"] --> Discovery
    
    subgraph Discovery["🔍 DISCOVERY ENGINE"]
        DatabaseCheck["🗃️ Database Check<br/>Pinecone.find_by_name()"]
        
        DatabaseCheck -->|Found| ExistingFlow["📊 Existing Company Flow"]
        DatabaseCheck -->|Not Found| UnknownFlow["❓ Unknown Company Flow"]
    end
    
    subgraph ExistingFlow["📊 EXISTING COMPANY ANALYSIS"]
        ContextualLLM["🧠 LLM Contextual Discovery<br/>Use company description<br/>Generate search terms<br/>Industry analysis"]
        VectorSearch["📐 Vector Similarity Search<br/>Embedding comparison<br/>Cosine similarity<br/>Industry filtering"]
        
        ContextualLLM --> Combine
        VectorSearch --> Combine
    end
    
    subgraph UnknownFlow["❓ UNKNOWN COMPANY ANALYSIS"]
        InferLLM["🔮 LLM Inference<br/>Predict industry<br/>Infer business model<br/>Generate search strategy"]
        SemanticSearch["🔍 Semantic Discovery<br/>Industry-based matching<br/>Business model similarity<br/>Market positioning"]
        
        InferLLM --> SemanticSearch
        SemanticSearch --> Combine
    end
    
    subgraph Enhancement["✨ RESULT ENHANCEMENT"]
        Combine["🔗 Combine & Deduplicate<br/>Merge LLM + Vector results<br/>Remove duplicates<br/>Rank by relevance"]
        Research["📋 Research Status Check<br/>Database metadata<br/>Processing history<br/>Availability assessment"]
        Format["📊 Format Results<br/>Confidence scores<br/>Reasoning explanations<br/>Business context"]
        
        Combine --> Research
        Research --> Format
    end
    
    Format --> Response["📤 JSON Response<br/>Similarity scores<br/>Discovery methods<br/>Research status<br/>Business relationships"]
    
    Response --> UI["🎨 UI Display<br/>Discovery cards<br/>Website links<br/>Research buttons<br/>Real-time updates"]
    
    %% Styling
    classDef inputStyle fill:#ff6b6b,stroke:#ff4757,stroke-width:3px,color:#ffffff
    classDef discoveryStyle fill:#ffa502,stroke:#ff6348,stroke-width:2px,color:#ffffff
    classDef existingStyle fill:#2ed573,stroke:#20bf6b,stroke-width:2px,color:#ffffff
    classDef unknownStyle fill:#5352ed,stroke:#3742fa,stroke-width:2px,color:#ffffff
    classDef enhanceStyle fill:#8e44ad,stroke:#9b59b6,stroke-width:2px,color:#ffffff
    classDef outputStyle fill:#e67e22,stroke:#d35400,stroke-width:2px,color:#ffffff
    
    class UserInput inputStyle
    class DatabaseCheck discoveryStyle
    class ContextualLLM,VectorSearch existingStyle
    class InferLLM,SemanticSearch unknownStyle
    class Combine,Research,Format enhanceStyle
    class Response,UI outputStyle
```

## 🤖 AI Model Hierarchy & Data Flow

```mermaid
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#ff6b6b',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#ff4757',
    'lineColor': '#ffa502',
    'secondaryColor': '#2ed573',
    'tertiaryColor': '#5352ed',
    'background': '#2f3542',
    'mainBkg': '#2f3542',
    'secondBkg': '#57606f'
  }
}}%%

graph LR
    subgraph Models["🤖 AI MODEL HIERARCHY"]
        direction TB
        Primary["🥇 PRIMARY<br/>Gemini 2.5 Pro<br/>Content Aggregation<br/>1M Token Context"]
        Fast["⚡ FAST<br/>Gemini 2.5 Flash<br/>Page Selection<br/>Quick Analysis"]
        CostOpt["💰 COST-OPTIMIZED<br/>AWS Nova Pro<br/>6x Cheaper<br/>Research Operations"]
        Fallback["🔄 FALLBACK<br/>OpenAI GPT-4o-mini<br/>Error Recovery<br/>Backup Processing"]
    end
    
    subgraph Processing["⚙️ PROCESSING TASKS"]
        direction TB
        LinkAnalysis["🔗 Link Analysis<br/>Page Selection<br/>URL Prioritization"]
        ContentAgg["📝 Content Aggregation<br/>Multi-page Analysis<br/>Sales Intelligence"]
        CompanyAnalysis["🏢 Company Analysis<br/>Industry Classification<br/>Business Model"]
        ResearchOps["📊 Research Operations<br/>Structured Prompts<br/>Cost-efficient Analysis"]
    end
    
    subgraph Storage["🗃️ DATA STORAGE"]
        direction TB
        VectorDB["📐 Vector Database<br/>Pinecone<br/>1536 Dimensions"]
        Metadata["📋 Metadata<br/>Essential Fields<br/>Search Optimized"]
        FullData["🗄️ Full Company Data<br/>Complete Information<br/>Analysis Results"]
    end
    
    %% Model to Task Assignments
    Fast --> LinkAnalysis
    Primary --> ContentAgg
    CostOpt --> ResearchOps
    Fallback --> CompanyAnalysis
    
    %% Processing to Storage
    LinkAnalysis --> VectorDB
    ContentAgg --> FullData
    CompanyAnalysis --> Metadata
    ResearchOps --> VectorDB
    
    %% Error Handling Flow
    Primary -.->|Error| CostOpt
    CostOpt -.->|Error| Fallback
    Fast -.->|Error| Primary
    
    %% Performance Indicators
    Processing --> Metrics["📊 PERFORMANCE METRICS<br/>• 670+ links discovered<br/>• 10-50 pages selected<br/>• 10 concurrent extractions<br/>• 25-60 second processing<br/>• 72% storage optimization"]
    
    %% Styling
    classDef primaryStyle fill:#2ed573,stroke:#20bf6b,stroke-width:3px,color:#ffffff
    classDef fastStyle fill:#ffa502,stroke:#ff6348,stroke-width:2px,color:#ffffff
    classDef costStyle fill:#5352ed,stroke:#3742fa,stroke-width:2px,color:#ffffff
    classDef fallbackStyle fill:#8e44ad,stroke:#9b59b6,stroke-width:2px,color:#ffffff
    classDef taskStyle fill:#ff6b6b,stroke:#ff4757,stroke-width:2px,color:#ffffff
    classDef storageStyle fill:#34495e,stroke:#2c3e50,stroke-width:2px,color:#ffffff
    classDef metricsStyle fill:#e67e22,stroke:#d35400,stroke-width:2px,color:#ffffff
    
    class Primary primaryStyle
    class Fast fastStyle
    class CostOpt costStyle
    class Fallback fallbackStyle
    class LinkAnalysis,ContentAgg,CompanyAnalysis,ResearchOps taskStyle
    class VectorDB,Metadata,FullData storageStyle
    class Metrics metricsStyle
```

## 📊 Real-time Progress Tracking

```mermaid
%%{init: {
  'theme': 'dark',
  'themeVariables': {
    'primaryColor': '#ff6b6b',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#ff4757',
    'lineColor': '#ffa502',
    'secondaryColor': '#2ed573',
    'tertiaryColor': '#5352ed',
    'background': '#2f3542',
    'mainBkg': '#2f3542',
    'secondBkg': '#57606f'
  }
}}%%

sequenceDiagram
    participant User as 👤 User
    participant UI as 🎨 Web UI
    participant API as 🔗 Flask API
    participant Logger as 📊 Progress Logger
    participant Scraper as 🕷️ Intelligent Scraper
    participant AI as 🤖 AI Models
    participant DB as 🗃️ Pinecone DB
    
    User->>UI: Submit Company for Processing
    UI->>API: POST /api/process-company
    API->>Logger: start_company_processing(job_id)
    API->>Scraper: scrape_company(company_data)
    
    Note over Logger: 📝 Thread-safe logging with emoji prefixes
    
    Scraper->>Logger: 🔍 PHASE 1: Link Discovery - RUNNING
    Scraper->>Scraper: robots.txt + sitemap + recursive crawl
    Scraper->>Logger: 🔍 PHASE 1: Link Discovery - COMPLETED (670 links)
    Logger-->>UI: Real-time update via SSE
    
    Scraper->>Logger: 🎯 PHASE 2: Page Selection - RUNNING
    Scraper->>AI: Analyze links with Gemini 2.5 Flash
    AI-->>Scraper: Selected 25 most valuable pages
    Scraper->>Logger: 🎯 PHASE 2: Page Selection - COMPLETED (25 pages)
    Logger-->>UI: Real-time update via SSE
    
    Scraper->>Logger: 📄 PHASE 3: Content Extraction - RUNNING
    Note over Scraper: 10 concurrent Crawl4AI extractions
    Scraper->>Scraper: Parallel page processing
    Scraper->>Logger: 📄 PHASE 3: Content Extraction - COMPLETED (23 successful)
    Logger-->>UI: Real-time update via SSE
    
    Scraper->>Logger: 🧠 PHASE 4: AI Aggregation - RUNNING
    Scraper->>AI: Gemini 2.5 Pro with 1M context
    AI-->>Scraper: Sales intelligence summary (2847 chars)
    Scraper->>Logger: 🧠 PHASE 4: AI Aggregation - COMPLETED
    Logger-->>UI: Real-time update via SSE
    
    Scraper-->>API: Company data with sales intelligence
    API->>AI: Bedrock analysis for classification
    AI-->>API: Industry, business model, stage
    API->>AI: Generate vector embedding
    AI-->>API: 1536-dimension vector
    API->>DB: upsert_company(company_data)
    DB-->>API: Success confirmation
    
    API->>Logger: complete_company_processing(job_id, success=True)
    Logger-->>UI: Final status update
    UI-->>User: ✅ Processing Complete with Results
```

These high-contrast Mermaid diagrams provide clear visual documentation of Theodore's company data retrieval process, optimized for readability with distinct colors and comprehensive flow representations.