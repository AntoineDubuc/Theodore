# Theodore Codebase Cleanup Log

## Overview
This document tracks the cleanup and reorganization of Theodore's codebase, executed on December 2025. The cleanup focuses on consolidating the Antoine extraction system which has become the core of Theodore's company intelligence pipeline.

## Cleanup Phases

### Phase 1: Remove Broken Files ✅ COMPLETED
**Date:** December 8, 2025  
**Files Deleted:**
- `src/antoine_selection_broken.py` - Broken backup with syntax errors
- `src/antoine_extraction_broken.py` - Broken backup with syntax errors

**Reason:** These files were non-functional backups created during development and are no longer needed.

**Status:** Successfully deleted both files.

### Phase 2: Consolidate Scraper Implementations (Pending)
**Current Scrapers:**
- `src/antoine_scraper_adapter.py` - **ACTIVE** - Main integration point
- `src/intelligent_company_scraper.py` - Legacy Theodore scraper (to be archived)
- `src/intelligent_company_scraper_FIXED.py` - Fixed version, unused (to be archived)
- `src/concurrent_intelligent_scraper.py` - Concurrent version, unused (to be archived)
- `src/specialized_page_scraper.py` - Specialized scraper, unused (to be archived)
- `src/experimental/crawl4ai_scraper.py` - Experimental, unused (to be archived)

**Plan:** Move all unused scrapers to `src/legacy/scrapers/`

### Phase 3: Reorganize Antoine Core Files (Pending)
**Antoine 4-Phase Pipeline:**
1. `antoine_discovery.py` - Phase 1: Link discovery (robots.txt, sitemap, headers)
2. `antoine_selection.py` - Phase 2: LLM-powered page selection
3. `antoine_crawler.py` - Phase 3: Content extraction with Trafilatura
4. `antoine_extraction.py` - Phase 4: Field extraction with Nova Pro

**Plan:** Move to `src/core/extraction/` to better reflect their central role

### Phase 4: Archive Old Directories (Pending)
**Directories to Archive:**
- `v2/antoine/` - Older implementation
- `v3/` - Another version
- `antoine/` - Standalone batch/test directory

**Plan:** Move to `archive/antoine_versions/`

## Active System Architecture After Cleanup

```
Theodore Intelligence Pipeline
├── app.py (Flask Web UI)
├── src/main_pipeline.py (Orchestration)
└── src/antoine_scraper_adapter.py (Integration)
    ├── Phase 1: antoine_discovery.py
    ├── Phase 2: antoine_selection.py  
    ├── Phase 3: antoine_crawler.py
    └── Phase 4: antoine_extraction.py
```

## Notes
- The Antoine system provides a sophisticated 4-phase extraction pipeline
- All changes preserve the working functionality
- Legacy code is archived, not deleted, for reference