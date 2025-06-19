# Theodore Research Architecture

## Overview

Theodore provides three distinct research workflows optimized for different use cases: discovery, verification, and deep intelligence gathering.

## Research Types

### 1. Find Similar Companies Research

**Purpose**: Quick discovery of companies similar to a target company
**Trigger**: "Find Similar Companies" or "Discover Similar Companies" button in UI

#### Flow
1. **Input**: 
   - Company name (mandatory)
   - Website URL (optional)

2. **Phase 1: Vector Database Query**
   - Query Pinecone index for semantically similar companies
   - Use existing company embeddings for fast similarity matching
   - Return ranked results based on business model, industry, size, etc.

3. **Phase 2: LLM Expansion** (conditional - if insufficient results)
   - Analyze Phase 1 results to understand similarity patterns
   - Ask LLM to generate additional similar companies based on discovered patterns
   - Use Google Search to find homepage URLs for LLM-suggested companies
   - **Surface scraping**: Extract company overview from homepage only
   - Combine LLM-generated companies with Pinecone results

4. **Output**: 
   - List of similar company cards
   - Each card includes: name, website, brief description, similarity score
   - Each card has "Research this company" button for deep dive

#### Technical Characteristics
- **Speed**: Fast (leverages existing data + minimal scraping)
- **Depth**: Surface-level information
- **Storage**: Temporary results, not persisted
- **LLM Usage**: Discovery and expansion when needed

---

### 2. Add a Company Research

**Purpose**: Comprehensive research and verification of a new company
**Trigger**: "Add a Company" button in UI

#### Flow
1. **Input**:
   - Company name (mandatory)
   - Website URL (optional)

2. **Verification Phase**:
   - Use Google Search to find/confirm the company's official website
   - Validate that the discovered URL represents the correct company

3. **Deep Crawling Phase** - 4-Phase Intelligent Scraping:
   
   **Phase 1: Link Discovery**
   - Parse robots.txt for additional paths and sitemaps
   - Analyze sitemap.xml for structured site navigation
   - Recursive crawling (3 levels deep, max 1000 links)
   - Filter and deduplicate discovered URLs

   **Phase 2: LLM Page Selection**
   - Analyze all discovered links using LLM
   - Prioritize pages likely to contain business intelligence:
     - Contact & Location: `/contact`, `/about`, `/get-in-touch`
     - Company Info: `/company`, `/our-story`, `/history`
     - Team & Leadership: `/team`, `/leadership`, `/management`
     - Business Intelligence: `/careers`, `/products`, `/services`
   - Select up to 50 most promising pages

   **Phase 3: Parallel Content Extraction**
   - Concurrent processing of selected pages (10 pages simultaneously)
   - Clean content extraction (remove nav, footer, scripts)
   - Target main content areas using specialized selectors
   - Respect crawling etiquette and rate limits

   **Phase 4: LLM Content Aggregation**
   - Combine content from all scraped pages
   - Use Gemini 2.5 Pro with 1M token context window
   - Generate structured business intelligence summary
   - Focus on sales-relevant information and company insights

4. **Data Processing**:
   - Generate embeddings using AWS Bedrock
   - Store in Pinecone vector database for future similarity searches
   - Apply business model and SaaS classification
   - Extract structured data fields (size, industry, location, etc.)

#### Technical Characteristics
- **Speed**: Slow (comprehensive analysis)
- **Depth**: Deep intelligence gathering
- **Storage**: Full persistence in Pinecone + detailed records
- **LLM Usage**: Page selection + comprehensive content analysis

---

### 3. Research Individual Similar Company

**Purpose**: Convert a discovered similar company into comprehensive intelligence
**Trigger**: "Research this company" button on similar company cards

#### Flow
- **Process**: Identical to "Add a Company" research flow
- **Input Source**: Company discovered through "Find Similar Companies"
- **Verification**: Same Google Search validation
- **Crawling**: Same 4-phase intelligent scraping system
- **Storage**: Same full persistence and classification

#### Technical Characteristics
- **Speed**: Slow (identical to Add Company)
- **Depth**: Deep intelligence gathering
- **Storage**: Full persistence in Pinecone + detailed records
- **LLM Usage**: Page selection + comprehensive content analysis

---

## Key Technical Distinctions

| Research Type | Crawling Depth | Data Sources | LLM Usage | Storage | Speed |
|---------------|----------------|--------------|-----------|---------|-------|
| **Find Similar** | Surface (homepage only) | Pinecone + Google Search | Discovery + expansion | Temporary | Fast |
| **Add Company** | Deep (4-phase system) | Google Search + full crawl | Page selection + analysis | Persistent | Slow |
| **Research Similar** | Deep (4-phase system) | Google Search + full crawl | Page selection + analysis | Persistent | Slow |

## Architecture Benefits

### Performance Optimization
- **Find Similar**: Leverages existing vector database for instant results
- **Deep Research**: Only runs when user explicitly requests comprehensive data
- **Hybrid Approach**: Balances discovery speed with intelligence depth

### User Experience
- **Progressive Disclosure**: Start with quick similar company discovery
- **On-Demand Depth**: Deep research only when needed
- **Clear Expectations**: Different buttons signal different research depths

### Resource Management
- **Efficient Discovery**: Minimal API calls for similarity search
- **Controlled Deep Research**: Full crawling only on user request
- **Smart Caching**: Pinecone serves as intelligent cache for similar company queries

## Current Implementation Status

### ✅ Working Components
- Pinecone vector database with company embeddings
- Google Search integration for website discovery
- Surface-level homepage scraping for similar company expansion
- UI components for all three research types

### ⚠️ Known Issues
- **Deep Research Hanging**: 4-phase intelligent scraping hangs at LLM Page Selection
- **Async/Sync Conflicts**: Mixed execution contexts cause deadlocks
- **Subprocess Issues**: LLM calls hang when executed in subprocess

### 🎯 Implementation Priority
1. **Implement Find Similar Companies** (bypasses hanging scraper)
2. **Fix deep research hanging issue** (architectural refactor needed)
3. **Optimize performance and user experience**

## Future Enhancements

### Intelligence Improvements
- **Real-time Similarity**: Live similarity scoring during research
- **Competitive Analysis**: Automated competitor identification
- **Market Mapping**: Visual similarity clusters and market positioning

### Performance Optimizations
- **Incremental Updates**: Update existing company data without full re-scrape
- **Smart Scheduling**: Background research for high-priority similar companies
- **Caching Strategies**: Multi-tier caching for different research depths