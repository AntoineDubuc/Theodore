# Research New Company Flow - Complete Documentation

**Date:** June 18, 2025  
**Status:** Implementation Plan for Rate-Limited Solution  
**Target:** Fix hanging "Add Company" and "Research this company" functionality  

## 📋 Overview

The Research New Company flow represents Theodore's most comprehensive company analysis capability, providing deep intelligence gathering through sophisticated web crawling and AI-powered content analysis. This flow is triggered by two primary UI actions and represents the core value proposition of Theodore's sales intelligence platform.

### Flow Types Covered

**1. "Add a Company" Research**
- **Trigger:** "Add New Company" tab → "Generate Sales Intelligence" button
- **UI Location:** `templates/index.html` lines 217-330
- **Purpose:** Add new companies to Theodore's database with comprehensive intelligence

**2. "Research Individual Similar Company"**  
- **Trigger:** "Research this company" buttons on similar company cards
- **Purpose:** Convert discovered companies into comprehensive intelligence records

Both flows use identical processing logic and produce the same comprehensive `CompanyData` objects.

## ⚠️ Current Critical Issue

**HANGING PROBLEM:** The research flow currently hangs indefinitely at **Phase 2: LLM Page Selection**

**Current Code Path (HANGS):**
```
User Action → POST /api/research → pipeline.process_single_company() → scraper.scrape_company() → Phase 2 LLM Call → ♾️ HANGS
```

**Root Cause:** Async/subprocess execution conflicts cause LLM calls to deadlock in mixed threading contexts.

## 🏗️ Complete 7-Phase Research Flow

### Phase 0: Input Validation & Website Verification

**Purpose:** Validate input and confirm company website  
**Duration:** ~5-10 seconds  
**LLM Usage:** None (no hanging risk)

**Process:**
1. **Input Validation**
   - Validate company name (required)
   - Validate website URL format (optional)
   - Sanitize inputs for security

2. **Google Search Verification** 
   - Use Google Search API to find/confirm official website
   - Validate discovered URL represents correct company
   - Handle ambiguous company names with multiple results

**Code Location:** Currently in `main_pipeline.py` `_get_or_create_company()`

**Input:**
```python
company_name: str  # "Stripe" 
website: str       # "https://stripe.com" (optional)
job_id: str        # Progress tracking ID
```

**Output:**
```python
verified_website: str    # Confirmed official website URL
company_exists: bool     # Whether company already in database
```

---

### Phase 1: Link Discovery

**Purpose:** Comprehensive discovery of all relevant pages on company website  
**Duration:** ~10-20 seconds  
**LLM Usage:** None (no hanging risk)

**Process:**
1. **robots.txt Analysis**
   - Parse robots.txt for additional paths and sitemaps
   - Identify crawling restrictions and allowed paths
   - Extract sitemap URLs for structured discovery

2. **Sitemap.xml Processing**
   - Parse XML sitemaps for structured site navigation
   - Extract URLs for all major site sections
   - Handle nested sitemaps and sitemap indexes

3. **Recursive Web Crawling**
   - Crawl 3 levels deep from homepage
   - Discover up to 1,000 unique URLs
   - Target critical business pages:
     - `/about`, `/company`, `/our-story`
     - `/contact`, `/get-in-touch`, `/locations`
     - `/team`, `/leadership`, `/management`
     - `/careers`, `/jobs`, `/culture`
     - `/products`, `/services`, `/solutions`
     - `/investors`, `/press`, `/news`

4. **URL Filtering & Deduplication**
   - Remove duplicate URLs and parameters
   - Filter out irrelevant pages (legal, privacy, etc.)
   - Prioritize business intelligence pages

**Technical Implementation:**
- **Working Code:** `IntelligentCompanyScraper.discover_pages_intelligent()`
- **HTTP Requests:** Direct requests (no LLM calls)
- **Performance:** Well-optimized with proper timeouts

**Output:**
```python
discovered_links: List[str]  # Up to 1,000 discovered URLs
link_categories: Dict[str, List[str]]  # Categorized by page type
discovery_metadata: Dict[str, Any]     # Stats and quality metrics
```

---

### Phase 2: LLM Page Selection ⚠️ **CRITICAL HANGING ISSUE**

**Purpose:** Intelligently select 10-50 most valuable pages for content extraction  
**Duration:** **♾️ CURRENTLY HANGS** → Should be ~8 seconds with rate limiting  
**LLM Usage:** 1 LLM call (Gemini 2.5 Flash) ← **HANGING POINT**

**Process:**
1. **Link Analysis Prompt**
   - Send all discovered links to LLM for analysis
   - Use specialized prompt to prioritize business intelligence pages
   - Request selection of 10-50 most promising URLs

2. **Intelligent Prioritization**
   - Prioritize pages likely to contain:
     - **Contact & Location data:** contact pages, about pages
     - **Company founding information:** history, our-story sections  
     - **Employee count indicators:** team, careers, about pages
     - **Leadership information:** team, management pages
     - **Business intelligence:** products, services, competitive info

3. **Fallback Strategy**
   - If LLM fails, use heuristic selection based on URL patterns
   - Ensure critical page types are always included

**Current Implementation (HANGS):**
```python
# This call hangs in subprocess/async context
selected_pages = gemini_client.analyze_page_selection(discovered_links)
```

**Rate-Limited Solution:**
```python
# Replace with rate-limited approach
task = LLMTask(
    task_id=f"page_selection_{company_name}_{timestamp}",
    prompt=page_selection_prompt,
    context={"discovered_links": discovered_links}
)
result = llm_manager.worker_pool.process_task(task)
selected_pages = result.selected_pages
```

**LLM Prompt (Reuse Existing):**
```
Analyze these discovered website links and select the 10-50 most valuable pages for business intelligence extraction.

Prioritize pages containing:
- Contact information and company locations
- Company history, founding information, and timeline
- Team members, leadership, and organizational structure  
- Products, services, and business model details
- Career pages indicating company size and culture

Links to analyze: {discovered_links}

Return selected URLs in JSON format with reasoning for each selection.
```

**Output:**
```python
selected_pages: List[str]           # 10-50 most valuable URLs
selection_reasoning: Dict[str, str] # Why each page was selected
llm_processing_time: float          # Performance tracking
```

---

### Phase 3: Parallel Content Extraction

**Purpose:** Extract clean, structured content from selected pages  
**Duration:** ~30-60 seconds  
**LLM Usage:** None (no hanging risk)

**Process:**
1. **Concurrent Page Processing**
   - Process 10 pages simultaneously using semaphore limiting
   - Use Crawl4AI with Chromium browser for JavaScript execution
   - Extract main content while removing navigation, footer, scripts

2. **Content Optimization**
   - Target main content areas: `main`, `article`, `.content`, `.main-content`
   - Remove boilerplate: navigation, footers, scripts, styles
   - Limit content to 10,000 characters per page
   - Clean and normalize text formatting

3. **Quality Assessment**
   - Validate content extraction success
   - Track content length and quality metrics
   - Handle extraction failures gracefully

**Technical Implementation:**
- **Working Code:** `IntelligentCompanyScraper._extract_content_parallel()`
- **Crawl4AI Integration:** Handles JavaScript-heavy modern websites
- **Performance:** Well-optimized with proper resource management

**Output:**
```python
extracted_content: List[Dict[str, str]]  # Content from each page
content_stats: Dict[str, Any]            # Quality and performance metrics
successful_extractions: int             # Number of successful extractions
```

---

### Phase 4: LLM Content Aggregation ⚠️ **POTENTIAL HANGING ISSUE**

**Purpose:** Analyze all extracted content and generate structured business intelligence  
**Duration:** **Potential hanging** → Should be ~12-15 seconds with rate limiting  
**LLM Usage:** 1 LLM call (Gemini 2.5 Pro) ← **POTENTIAL HANGING POINT**

**Process:**
1. **Content Consolidation**
   - Combine content from all extracted pages (up to 5,000 chars each)
   - Use Gemini 2.5 Pro with 1M token context window
   - Analyze complete website content for comprehensive insights

2. **Structured Intelligence Generation**
   - Generate 2-3 paragraph business intelligence summary
   - Extract structured data fields:
     - Company overview and value proposition
     - Business model and revenue approach  
     - Target market and customer segments
     - Products/services and competitive advantages
     - Company maturity and sales context

3. **Quality Validation**
   - Ensure response contains required fields
   - Validate JSON structure and data types
   - Handle incomplete or failed analysis

**Current Implementation (MAY HANG):**
```python
# This call may hang in subprocess context
business_intelligence = gemini_client.analyze_complete_content(all_content)
```

**Rate-Limited Solution:**
```python
# Replace with rate-limited approach
task = LLMTask(
    task_id=f"content_analysis_{company_name}_{timestamp}",
    prompt=content_analysis_prompt,
    context={"extracted_content": all_content}
)
result = llm_manager.worker_pool.process_task(task)
business_intelligence = result.structured_data
```

**LLM Prompt (Reuse Existing):**
```
Analyze this comprehensive website content and generate structured business intelligence for sales purposes.

Website Content: {extracted_content}

Generate a structured analysis including:
- Company overview and value proposition
- Business model (B2B/B2C/B2B2C) and target market
- Key products/services and competitive advantages
- Company size indicators and maturity stage
- Sales-relevant insights and market context

Return structured data in JSON format with comprehensive business intelligence summary.
```

**Output:**
```python
company_description: str      # 2-3 paragraph business summary
industry: str                 # Primary industry classification  
business_model: str           # B2B/B2C/B2B2C classification
target_market: str           # Primary customer segments
key_services: List[str]      # Main products/services
company_size: str            # Size indicators and stage
value_proposition: str       # Core value proposition
competitive_advantages: str  # Key differentiators
```

---

### Phase 5: Data Processing & Enhancement

**Purpose:** Enhance extracted data and prepare for storage  
**Duration:** ~10-15 seconds  
**LLM Usage:** Classification system (AWS Bedrock) ← **Rate limiting may be needed**

**Process:**
1. **Business Intelligence Enhancement**
   - Apply extracted intelligence to company data structure
   - Populate all available `CompanyData` fields
   - Generate comprehensive company profile

2. **SaaS Business Model Classification**
   - Use `SaaSBusinessModelClassifier` with AWS Bedrock
   - Classify company as SaaS vs Non-SaaS
   - Assign specific category (FinTech, HealthTech, etc.)
   - Generate confidence score and justification

3. **Embedding Generation**
   - Create embedding text from company description
   - Generate 1536-dimension vector using AWS Bedrock
   - Prepare for similarity search and clustering

**Technical Implementation:**
- **Classification:** `classification/saas_classifier.py`
- **Embeddings:** `bedrock_client.generate_embedding()`
- **Data Models:** `models.py` `CompanyData` structure

**Output:**
```python
enhanced_company: CompanyData         # Complete company data object
saas_classification: str             # SaaS category classification
classification_confidence: float     # Confidence score (0.0-1.0)
embedding: List[float]               # 1536-dimension vector
```

---

### Phase 6: Storage & Persistence

**Purpose:** Store comprehensive company data for future similarity searches  
**Duration:** ~5-10 seconds  
**LLM Usage:** None (no hanging risk)

**Process:**
1. **Database Storage**
   - Store complete `CompanyData` object in Pinecone vector database
   - Include all extracted intelligence and metadata
   - Enable future similarity searches and clustering

2. **Metadata Management**
   - Store essential metadata for filtering and search
   - Include classification, industry, business model
   - Add processing timestamps and quality indicators

3. **Verification**
   - Confirm successful storage in Pinecone
   - Validate data retrieval and search functionality
   - Update company status and research completion

**Technical Implementation:**
- **Vector Storage:** `pinecone_client.upsert_company()`
- **Metadata:** Essential fields optimized for search
- **Quality Assurance:** Verification and validation

**Output:**
```python
storage_success: bool            # Successful Pinecone storage
database_id: str                 # Pinecone vector ID
company_data: CompanyData        # Final complete company object
research_status: str             # "completed" or "failed"
```

## 🔧 Rate-Limited Implementation Strategy

### Core Solution: Replace Hanging LLM Calls

**Phase 2 & Phase 4 require rate-limited LLM management:**

```python
class RateLimitedResearchNewCompanyFlow:
    def __init__(self):
        # Use proven rate-limited approach
        self.llm_manager = RateLimitedTheodoreLLMManager(
            max_workers=1,
            requests_per_minute=8  # Conservative for Gemini free tier
        )
        
        # Theodore integration (reuse existing)
        self.pinecone_client = PineconeClient(...)
        self.bedrock_client = BedrockClient()
        
    def process_single_company(self, company_name: str, website: str, job_id: str = None) -> CompanyData:
        """
        EXACT replacement for pipeline.process_single_company()
        Same interface, same return type, no hanging issues
        """
        # Phase 0-1: Reuse existing (no LLM calls)
        # Phase 2: Rate-limited LLM page selection
        # Phase 3: Reuse existing (no LLM calls)  
        # Phase 4: Rate-limited LLM content aggregation
        # Phase 5-6: Reuse existing with potential rate limiting for classification
```

### Expected Performance Transformation

**Current State (HANGING):**
```
Phase 1: Link Discovery (15s)
Phase 2: LLM Page Selection (♾️ HANGS INDEFINITELY)
Phase 3: Never reached
Phase 4: Never reached  
Phase 5: Never reached
Phase 6: Never reached
Total: ♾️ INFINITE HANGING
```

**After Rate-Limited Implementation:**
```
Phase 0: Verification (8s)
Phase 1: Link Discovery (15s) 
Phase 2: LLM Page Selection (8s) ← FIXED WITH RATE LIMITING
Phase 3: Content Extraction (45s)
Phase 4: LLM Content Aggregation (12s) ← RATE LIMITED
Phase 5: Data Processing (12s)
Phase 6: Storage (8s)
Total: ~108s (1.8 minutes) ← PREDICTABLE COMPLETION
```

## 🎯 Integration Requirements

### API Compatibility
- **Endpoint:** `/api/research` (no changes)
- **Request Format:** Same JSON structure
- **Response Format:** Same `CompanyData` object
- **Progress Tracking:** Same 4-phase UI updates

### Data Structure Compatibility
- **CompanyData Model:** Identical field structure
- **Pinecone Storage:** Same metadata format
- **Classification:** Same SaaS categorization
- **Embeddings:** Same 1536-dimension vectors

### UI Compatibility
- **Progress Container:** Same 4-phase display
- **Result Cards:** Same enhanced data display
- **Error Handling:** Same user-friendly messages
- **Timeout Management:** Improved predictable timing

## 🚨 Critical Success Factors

### 1. Eliminate Hanging Issues
- **Root Cause:** LLM calls in subprocess/async contexts
- **Solution:** Rate-limited LLM management with proper thread isolation
- **Validation:** 100% completion rate for research requests

### 2. Preserve Data Quality
- **Intelligence Extraction:** Same comprehensive business analysis
- **Structured Data:** All existing CompanyData fields populated
- **Classification Accuracy:** Maintain SaaS categorization quality

### 3. Maintain Performance
- **Predictable Timing:** 1.5-3 minutes vs infinite hanging
- **Resource Efficiency:** Controlled memory and CPU usage
- **Rate Limit Compliance:** Zero API quota breaches

### 4. Ensure Compatibility
- **Zero UI Changes:** Existing interface works seamlessly
- **API Stability:** Same request/response patterns
- **Database Schema:** No changes to storage format

This comprehensive flow documentation provides the foundation for implementing a reliable, rate-limited research new company system that eliminates hanging issues while preserving all existing functionality and data quality.