# Theodore Current Architecture & Features

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                THEODORE PLATFORM                                │
│                        AI-Powered Company Intelligence                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌──────────────────────────────────────────────────────────┐
│   INPUT     │    │                    CORE PIPELINE                         │
│             │    │                                                          │
│ Company URL │───▶│  ┌─────────────────────────────────────────────────────┐ │
│ Survey CSV  │    │  │            TheodoreIntelligencePipeline             │ │
│ Single Co.  │    │  │                                                     │ │
└─────────────┘    │  │  • Orchestrates entire workflow                    │ │
                   │  │  • Batch processing (400+ companies)               │ │
                   │  │  • Error handling & recovery                       │ │
                   │  │  • Progress tracking                               │ │
                   │  └─────────────────────────────────────────────────────┘ │
                   └──────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          INTELLIGENT WEB SCRAPING                               │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      Crawl4AICompanyScraper                             │   │
│  │                                                                         │   │
│  │  Multi-Page Discovery Strategy:                                        │   │
│  │  Searches for 11 target page types, crawls all found pages:           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │   │
│  │  │ Homepage │ │   About  │ │ Services │ │   Team   │ │ Contact  │ ... │   │
│  │  │ Priority │ │ Priority │ │ Priority │ │ Priority │ │ Priority │     │   │
│  │  │   1.0    │ │   0.9    │ │   0.7    │ │   0.6    │ │   0.2    │     │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘     │   │
│  │                                                                         │   │
│  │  Features:                                                              │   │
│  │  • CSS selector targeting                                               │   │
│  │  • Smart chunking (800-2500 tokens)                                    │   │
│  │  • Company-specific caching                                             │   │
│  │  • Rate limiting & error recovery                                       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        AI-POWERED EXTRACTION                                    │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                       OpenAI GPT-4o-mini                                │   │
│  │                                                                         │   │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │   │
│  │  │              Pydantic Schema Extraction                          │ │   │
│  │  │                                                                   │ │   │
│  │  │  CompanyIntelligence Schema (11 fields):                         │ │   │
│  │  │  • company_name      • business_model                            │ │   │
│  │  │  • industry          • target_market                             │ │   │
│  │  │  • key_services      • tech_stack                                │ │   │
│  │  │  • location          • leadership_team                           │ │   │
│  │  │  • founding_year     • value_proposition                         │ │   │
│  │  │  • company_description                                           │ │   │
│  │  └───────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                         │   │
│  │  Features:                                                              │   │
│  │  • Priority-weighted data merging                                      │   │
│  │  • 95% extraction success rate                                         │   │
│  │  • Cost: $0.08-0.12 per company                                        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         BUSINESS INTELLIGENCE                                   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    AWS Bedrock Integration                              │   │
│  │                                                                         │   │
│  │  ┌─────────────────────────┐    ┌─────────────────────────────────────┐ │   │
│  │  │    Amazon Nova Premier  │    │        Amazon Titan Embeddings     │ │   │
│  │  │                         │    │                                     │ │   │
│  │  │  • Deep business        │    │  • 1536-dimensional vectors        │ │   │
│  │  │    analysis             │    │  • Semantic understanding          │ │   │
│  │  │  • Sector insights      │    │  • Company similarity             │ │   │
│  │  │  • Strategic context    │    │  • Industry clustering            │ │   │
│  │  └─────────────────────────┘    └─────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           RAG SYSTEM & VECTOR STORAGE                           │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         PineconeClient                                  │   │
│  │                                                                         │   │
│  │  Storage Strategy (92% cost reduction):                                 │   │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │   │
│  │  │                    Vector Index                                   │ │   │
│  │  │                                                                   │ │   │
│  │  │  Metadata (5 essential fields):                                  │ │   │
│  │  │  • company_name                                                   │ │   │
│  │  │  • industry                                                       │ │   │
│  │  │  • business_model                                                 │ │   │
│  │  │  • location                                                       │ │   │
│  │  │  • key_services                                                   │ │   │
│  │  │                                                                   │ │   │
│  │  │  + 1536D embedding vector                                         │ │   │
│  │  └───────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                         │   │
│  │  RAG Capabilities:                                                      │   │
│  │  • Semantic company search                                             │   │
│  │  • Business model similarity                                           │   │
│  │  • Industry clustering                                                 │   │
│  │  • Technology stack matching                                           │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       CLUSTERING & ANALYSIS ENGINE                              │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                   SectorClusteringEngine                               │   │
│  │                                                                         │   │
│  │  Clustering Methods:                                                    │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │   │
│  │  │   Industry-     │    │   Embedding-    │    │   Intelligent   │     │   │
│  │  │     Based       │    │     Based       │    │    Merging      │     │   │
│  │  │   Clustering    │    │   Similarity    │    │   & Quality     │     │   │
│  │  │                 │    │   Clustering    │    │   Validation    │     │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘     │   │
│  │                                                                         │   │
│  │  Features:                                                              │   │
│  │  • Optimal cluster estimation                                           │   │
│  │  • Company-to-company similarity                                        │   │
│  │  • Sector cohesion analysis                                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUT & RESULTS                                   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      Structured Data Models                             │   │
│  │                                                                         │   │
│  │  CompanyData (62+ fields):                                              │   │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐           │   │
│  │  │   Basic Info    │ │  AI Analysis    │ │   Embeddings    │           │   │
│  │  │                 │ │                 │ │                 │           │   │
│  │  │ • Name          │ │ • Intelligence  │ │ • Vector        │           │   │
│  │  │ • Industry      │ │ • Insights      │ │ • Similarity    │           │   │
│  │  │ • Location      │ │ • Sector data   │ │ • Clusters      │           │   │
│  │  │ • Tech stack    │ │ • Quality       │ │ • Metadata      │           │   │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘           │   │
│  │                                                                         │   │
│  │  Export Formats:                                                        │   │
│  │  • CSV for business users                                               │   │
│  │  • JSON for API integration                                             │   │
│  │  • HubSpot-ready format                                                 │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

## Key Performance Metrics

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SYSTEM PERFORMANCE                                 │
│                                                                                 │
│  Processing Speed:    ~77 seconds per company (variable pages discovered)      │
│  Success Rate:        95% completion with error recovery                       │
│  Cost Efficiency:     $0.08-0.12 per company                                   │
│  Storage Optimization: 92% reduction in vector storage costs                   │
│  Extraction Accuracy: 85-95% (vs 40-60% with regex)                           │
│  Batch Capability:   400+ companies automated processing                       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

## Core Value Proposition

**Problem Solved**: Transform David's manual 5-6 hour research process for 400 companies into automated background processing

**Key Benefits**:
- **Scale**: Process hundreds of companies automatically  
- **Quality**: AI-powered structured extraction vs manual research
- **Integration**: HubSpot API-ready output for seamless workflow
- **Intelligence**: RAG system enables semantic search and company discovery
- **Cost Effective**: Optimized AI usage and vector storage for production scale