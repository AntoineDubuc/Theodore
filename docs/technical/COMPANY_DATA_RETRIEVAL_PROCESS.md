# 🔄 Theodore Company Data Retrieval Process

This document provides a comprehensive overview of how Theodore retrieves and processes company data through its intelligent pipeline.

## 📊 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           THEODORE COMPANY DATA RETRIEVAL PIPELINE                  │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   USER INPUT    │    │   DISCOVERY     │    │   PROCESSING    │    │   STORAGE &     │
│                 │    │   PATHWAYS      │    │   PIPELINE      │    │   RETRIEVAL     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼

┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 1. USER INTERACTION LAYER                                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐                  │
│  │  Discovery Tab  │   │  Process Tab    │   │  Database Tab   │                  │
│  │                 │   │                 │   │                 │                  │
│  │ • Company Name  │   │ • Company Name  │   │ • Browse All    │                  │
│  │ • Find Similar  │   │ • Website URL   │   │ • Filter/Search │                  │
│  │                 │   │ • Process New   │   │ • View Details  │                  │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘                  │
│           │                       │                       │                       │
│           ▼                       ▼                       ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                     FLASK API ENDPOINTS                                     │  │
│  │                                                                             │  │
│  │ /api/discover    /api/process-company    /api/database    /api/companies   │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 2. DISCOVERY PATHWAYS                                                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                    SIMILARITY DISCOVERY WORKFLOW                            │  │
│  │                                                                             │  │
│  │  Company Name Input → SimpleEnhancedDiscovery                              │  │
│  │           │                      │                                         │  │
│  │           ▼                      ▼                                         │  │
│  │  ┌───────────────┐    ┌─────────────────────────────────────────────────┐  │  │
│  │  │ Database Check│    │           LLM DISCOVERY METHODS                 │  │  │
│  │  │               │    │                                                 │  │  │
│  │  │ Pinecone      │    │ 1. Contextual Discovery (for existing companies)│  │  │
│  │  │ find_by_name  │    │    • Use company description/industry           │  │  │
│  │  │               │    │    • Generate contextual search terms           │  │  │
│  │  └───────┬───────┘    │    • Find semantic matches                      │  │  │
│  │          │            │                                                 │  │  │
│  │          ▼            │ 2. Unknown Company Discovery                    │  │  │
│  │  ┌───────────────┐    │    • LLM infers industry/business model        │  │  │
│  │  │ IF FOUND:     │    │    • Generates search strategy                 │  │  │
│  │  │ Vector Search │    │    • Finds similar companies by inference      │  │  │
│  │  │ + LLM Context │    │                                                 │  │  │
│  │  │               │    │ 3. Vector Similarity Search                     │  │  │
│  │  │ IF NOT FOUND: │    │    • Embedding comparison                       │  │  │
│  │  │ LLM-only      │    │    • Cosine similarity ranking                 │  │  │
│  │  │ Discovery     │    │    • Industry/business model filtering         │  │  │
│  │  └───────────────┘    └─────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 3. INTELLIGENT PROCESSING PIPELINE                                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                   4-PHASE INTELLIGENT SCRAPING SYSTEM                       │  │
│  │                                                                             │  │
│  │  ┌───────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ PHASE 1: COMPREHENSIVE LINK DISCOVERY                                 │  │  │
│  │  │                                                                       │  │  │
│  │  │ robots.txt → sitemap.xml → recursive_crawling → up_to_1000_links     │  │  │
│  │  │     │              │              │                       │          │  │  │
│  │  │     ▼              ▼              ▼                       ▼          │  │  │
│  │  │ Additional    Structured     Navigation      Comprehensive          │  │  │
│  │  │ Paths +       Site Map       Links +         Link Set               │  │  │
│  │  │ Sitemaps                     Content                                 │  │  │
│  │  └───────────────────────────────────────────────────────────────────────┘  │  │
│  │                                    │                                      │  │
│  │                                    ▼                                      │  │
│  │  ┌───────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ PHASE 2: LLM-DRIVEN PAGE SELECTION                                   │  │  │
│  │  │                                                                       │  │  │
│  │  │ All_Discovered_Links → Gemini_2.5_Flash → Intelligent_Selection      │  │  │
│  │  │                               │                       │               │  │  │
│  │  │                               ▼                       ▼               │  │  │
│  │  │                     Analyze_Link_Patterns    Select_10-50_Pages       │  │  │
│  │  │                     • /contact, /about       • Highest_Value         │  │  │
│  │  │                     • /team, /careers        • Contact_Info          │  │  │
│  │  │                     • /products, /services   • Leadership_Data       │  │  │
│  │  │                     • Business_Intelligence  • Company_History       │  │  │
│  │  └───────────────────────────────────────────────────────────────────────┘  │  │
│  │                                    │                                      │  │
│  │                                    ▼                                      │  │
│  │  ┌───────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ PHASE 3: PARALLEL CONTENT EXTRACTION                                 │  │  │
│  │  │                                                                       │  │  │
│  │  │ Selected_URLs → Crawl4AI_AsyncWebCrawler → Parallel_Processing       │  │  │
│  │  │      │                     │                         │               │  │  │
│  │  │      ▼                     ▼                         ▼               │  │  │
│  │  │ 10_Concurrent       Chromium_Browser         Clean_Text_Extraction   │  │  │
│  │  │ Requests           JavaScript_Execution      Remove_Nav/Footer       │  │  │
│  │  │                    Dynamic_Content           Preserve_Main_Content   │  │  │
│  │  │                                                                       │  │  │
│  │  │ Real-time Progress Updates → Progress_Logger → Live_UI_Feedback      │  │  │
│  │  └───────────────────────────────────────────────────────────────────────┘  │  │
│  │                                    │                                      │  │
│  │                                    ▼                                      │  │
│  │  ┌───────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ PHASE 4: LLM CONTENT AGGREGATION                                     │  │  │
│  │  │                                                                       │  │  │
│  │  │ All_Page_Content → Gemini_2.5_Pro → Sales_Intelligence_Summary       │  │  │
│  │  │      │                    │                      │                   │  │  │
│  │  │      ▼                    ▼                      ▼                   │  │  │
│  │  │ Up_to_5000_chars    1M_Token_Context    2-3_Paragraph_Summary        │  │  │
│  │  │ Per_Page           Complete_Analysis    Business_Intelligence         │  │  │
│  │  │ Combined_Content   Company_Insights     Sales_Optimized              │  │  │
│  │  └───────────────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                         AI ANALYSIS & ENHANCEMENT                          │  │
│  │                                                                             │  │
│  │ Sales_Intelligence → AI_Model_Analysis → Structured_Data_Extraction         │  │
│  │                            │                         │                     │  │
│  │                            ▼                         ▼                     │  │
│  │                    Bedrock_Client              Company_Data_Object          │  │
│  │                    • Industry_Classification   • Business_Model            │  │
│  │                    • Business_Model_Analysis   • Target_Market             │  │
│  │                    • Market_Positioning        • Value_Proposition         │  │
│  │                    • Company_Stage_Assessment  • Technology_Stack          │  │
│  │                                                                             │  │
│  │ Enhanced_Extraction → Gemini_Client → Additional_Field_Extraction          │  │
│  │ (if_missing_data)         │                    │                           │  │
│  │                           ▼                    ▼                           │  │
│  │                    Detailed_Analysis    • Founding_Year                    │  │
│  │                    JSON_Parsing         • Employee_Count                   │  │
│  │                                        • Social_Media_Links               │  │
│  │                                        • Leadership_Team                  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 4. STORAGE & RETRIEVAL SYSTEM                                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                           VECTOR EMBEDDING GENERATION                       │  │
│  │                                                                             │  │
│  │ Company_Data → Embedding_Text_Preparation → Bedrock_Embedding_Generation    │  │
│  │     │                    │                           │                     │  │
│  │     ▼                    ▼                           ▼                     │  │
│  │ Structured_Fields   Text_Concatenation      1536_Dimension_Vector          │  │
│  │ • Description       • Name + Industry       Amazon_Titan_Embeddings        │  │
│  │ • Industry          • Business_Model        Semantic_Representation        │  │
│  │ • Business_Model    • Description                                          │  │
│  │ • Target_Market     • Key_Services                                         │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                           │
│                                       ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                           PINECONE VECTOR DATABASE                          │  │
│  │                                                                             │  │
│  │ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │  │
│  │ │   UPSERT OPS    │  │  RETRIEVAL OPS  │  │     SIMILARITY SEARCH       │  │  │
│  │ │                 │  │                 │  │                             │  │  │
│  │ │ • Store_Vector  │  │ • find_by_name  │  │ • Vector_Similarity         │  │  │
│  │ │ • Store_Metadata│  │ • find_by_id    │  │ • Cosine_Distance           │  │  │
│  │ │ • Update_Existing│ │ • get_all       │  │ • Industry_Filtering        │  │  │
│  │ │ • Deduplicate   │  │ • browse_paginated│ │ • Business_Model_Matching  │  │  │
│  │ └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │  │
│  │                                                                             │  │
│  │ Essential_Metadata_Fields (Optimized_Storage):                             │  │
│  │ • company_name, industry, business_model, location, company_size           │  │
│  │ • sales_intelligence_summary, research_status, last_updated               │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                           │
│                                       ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                           RETRIEVAL & PRESENTATION                          │  │
│  │                                                                             │  │
│  │ Database_Query → Data_Formatting → UI_Presentation                         │  │
│  │      │                 │                    │                              │  │
│  │      ▼                 ▼                    ▼                              │  │
│  │ • Search_by_Name   • JSON_Response     • Discovery_Cards                   │  │
│  │ • Similarity_Search • Company_Details  • Research_Modals                   │  │
│  │ • Browse_All       • Research_Status   • Database_Browser                  │  │
│  │ • Filter_Results   • Website_Links     • Real-time_Updates                 │  │
│  │                                                                             │  │
│  │ Real-time_Progress_Tracking:                                               │  │
│  │ Progress_Logger → SSE_Events → Live_UI_Updates                             │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Sequences

### 1. Discovery Workflow

```
User Input (Company Name)
    ↓
Flask /api/discover endpoint
    ↓
SimpleEnhancedDiscovery.discover_similar_companies()
    ↓
┌─ Database Check (Pinecone.find_company_by_name)
│     ├─ FOUND → LLM Contextual Discovery + Vector Similarity
│     └─ NOT FOUND → LLM-only Discovery (infer industry/business model)
    ↓
ResearchManager.enhance_discovered_companies()
    ↓
Format results with research_status, confidence, reasoning
    ↓
JSON Response → UI Display (Discovery Cards)
```

### 2. Company Processing Workflow

```
User Input (Company Name + Website)
    ↓
Flask /api/process-company endpoint
    ↓
TheodoreIntelligencePipeline.process_single_company()
    ↓
┌─ Get or Create Company (prevent duplicates)
    ↓
IntelligentCompanyScraperSync.scrape_company()
    ├─ Phase 1: Link Discovery (robots.txt + sitemap + recursive)
    ├─ Phase 2: LLM Page Selection (Gemini 2.5 Flash)
    ├─ Phase 3: Parallel Extraction (Crawl4AI + 10 concurrent)
    └─ Phase 4: Content Aggregation (Gemini 2.5 Pro + 1M context)
    ↓
BedrockClient.analyze_company_content()
    ├─ Industry Classification
    ├─ Business Model Analysis
    └─ Market Positioning
    ↓
Enhanced Extraction (if missing fields)
    ├─ GeminiClient.analyze_content()
    └─ JSON parsing for founding_year, employee_count, social_media
    ↓
BedrockClient.generate_embedding()
    ├─ Prepare embedding text (name + industry + description)
    └─ Amazon Titan Embeddings (1536 dimensions)
    ↓
PineconeClient.upsert_company()
    ├─ Store vector representation
    ├─ Store essential metadata
    └─ Update existing if duplicate
    ↓
Success Response → UI Update (Process Tab)
```

### 3. Database Retrieval Workflow

```
User Browse Request
    ↓
Flask /api/database endpoint
    ↓
PineconeClient.get_all_companies()
    ├─ Retrieve all vectors with metadata
    ├─ Extract essential fields
    └─ Sort by company name
    ↓
Enhance with detailed metadata
    ├─ Extract full company information
    ├─ Calculate statistics
    └─ Format for UI display
    ↓
JSON Response → Database Browser UI
    ├─ Company cards with website links
    ├─ Research status indicators
    └─ One-click access to company websites
```

## 🧩 Key Components Interaction

### AI Models Hierarchy

1. **Primary Analysis**: Gemini 2.5 Pro (1M context for content aggregation)
2. **Page Selection**: Gemini 2.5 Flash Preview (fast link analysis)  
3. **Cost-Optimized**: Amazon Nova Pro (6x cheaper for research)
4. **Fallback**: OpenAI GPT-4o-mini (when others fail)

### Storage Optimization

**Essential Metadata (5 fields):**
- `company_name`, `industry`, `business_model`, `location`, `company_size`

**vs Original Schema (62+ fields):**
- 72% storage reduction while maintaining search quality

### Real-time Progress System

```
Progress_Logger (Thread-safe)
    ↓
Phase-specific logging with emoji prefixes
    ├─ 🔍 LINK DISCOVERY
    ├─ 🎯 PAGE SELECTION  
    ├─ 📄 CONTENT EXTRACTION
    └─ 🧠 AI AGGREGATION
    ↓
Server-Sent Events (SSE) → Live UI Updates
```

## 📊 Performance Characteristics

- **Link Discovery**: Up to 1000 links per company
- **Page Selection**: 10-50 most valuable pages
- **Parallel Processing**: 10 concurrent extractions
- **Content Analysis**: 1M+ token context window
- **Vector Dimensions**: 1536 (Amazon Titan)
- **Processing Time**: 25-60 seconds per company
- **Storage Efficiency**: 72% metadata reduction

## 🔧 Error Handling & Fallbacks

1. **Graceful Degradation**: AI analysis → web search → manual fallback
2. **Timeout Management**: Tiered timeouts (UI: 25s, Testing: 60s)
3. **Progress Tracking**: Real-time status with detailed error messages
4. **Model Failover**: Primary → Cost-optimized → Fallback AI models

This comprehensive data retrieval process ensures Theodore can extract meaningful company intelligence using sophisticated AI methods while providing real-time feedback and maintaining high performance standards.