# Theodore API Endpoint Documentation

This document provides the correct usage for all Theodore API endpoints based on the actual implementation in `app.py`.

## 🔍 Search Endpoints

### GET /api/search
**Purpose:** Search existing companies in the database  
**Parameters:**
- `q` (query parameter, required): Search query string (minimum 2 characters)

**Correct Usage:**
```bash
curl -X GET 'http://localhost:5002/api/search?q=apple'
```

**Incorrect Usage:**
```bash
# ❌ Wrong parameter name
curl -X GET 'http://localhost:5002/api/search?query=apple'
```

**Response:**
```json
{
  "results": [
    {"company_name": "Apple Inc", "website": "https://apple.com"}
  ]
}
```

---

## 🔬 Research Endpoints

### POST /api/research
**Purpose:** Start company research using Theodore's AI pipeline  
**Content-Type:** application/json

**Required Data Structure:**
```json
{
  "company": {
    "name": "Company Name",
    "website": "https://company.com"
  }
}
```

**Correct Usage:**
```bash
curl -X POST http://localhost:5002/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "company": {
      "name": "Apple Inc",
      "website": "https://apple.com"
    }
  }'
```

**Incorrect Usage:**
```bash
# ❌ Wrong structure
curl -X POST http://localhost:5002/api/research \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Apple Inc"}'
```

### POST /api/research/prompts/estimate
**Purpose:** Estimate cost for research prompts  
**Content-Type:** application/json

**Required Data Structure:**
```json
{
  "selected_prompts": ["prompt1", "prompt2"]
}
```

**Correct Usage:**
```bash
curl -X POST http://localhost:5002/api/research/prompts/estimate \
  -H "Content-Type: application/json" \
  -d '{"selected_prompts": ["industry_analysis", "competitive_landscape"]}'
```

---

## 🔍 Discovery Endpoints

### POST /api/discover
**Purpose:** Find similar companies to a target company

**Required Data Structure:**
```json
{
  "company_name": "Target Company",
  "limit": 5
}
```

**Correct Usage:**
```bash
curl -X POST http://localhost:5002/api/discover \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Salesforce",
    "limit": 5
  }'
```

### POST /api/test-discovery
**Purpose:** Test discovery functionality

**Required Data Structure:**
```json
{
  "company_name": "Target Company"
}
```

---

## 🗄️ Database Endpoints

### GET /api/database
**Purpose:** Browse company database with pagination  
**Parameters (all optional):**
- `page` (query parameter): Page number (default: 1)
- `per_page` (query parameter): Items per page (default: 25)
- `search` (query parameter): Search filter

**Correct Usage:**
```bash
curl -X GET 'http://localhost:5002/api/database?page=1&per_page=25'
curl -X GET 'http://localhost:5002/api/database?search=tech'
```

### GET /api/companies/details
**Purpose:** Get detailed company information  
**Parameters:**
- `company_id` (query parameter, required): Company ID

**Correct Usage:**
```bash
curl -X GET 'http://localhost:5002/api/companies/details?company_id=12345'
```

---

## 📊 Progress Endpoints

### GET /api/progress/current
**Purpose:** Get current job progress  
**Parameters:** None required

**Correct Usage:**
```bash
curl -X GET http://localhost:5002/api/progress/current
```

### GET /api/progress/all
**Purpose:** Get all progress data  
**Parameters:** None required

**Correct Usage:**
```bash
curl -X GET http://localhost:5002/api/progress/all
```

---

## 🏷️ Classification Endpoints

### GET /api/classification/stats
**Purpose:** Get classification statistics  
**Parameters:** None required

**Correct Usage:**
```bash
curl -X GET http://localhost:5002/api/classification/stats
```

### POST /api/classify-unknown-industries
**Purpose:** Classify companies with unknown industries  
**Content-Type:** application/json  
**Note:** This is a long-running operation that may timeout

**Correct Usage:**
```bash
curl -X POST http://localhost:5002/api/classify-unknown-industries \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## ⚙️ Settings Endpoints

### GET /api/settings
**Purpose:** Get current system settings  
**Parameters:** None required

**Correct Usage:**
```bash
curl -X GET http://localhost:5002/api/settings
```

### POST /api/settings/health-check
**Purpose:** Perform system health check  
**Content-Type:** application/json

**Correct Usage:**
```bash
curl -X POST http://localhost:5002/api/settings/health-check \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## 📈 Field Metrics Endpoints

### GET /api/field-metrics/summary
**Purpose:** Get field metrics summary  
**Parameters:** None required

**Correct Usage:**
```bash
curl -X GET http://localhost:5002/api/field-metrics/summary
```

---

## 🔧 Common Issues & Fixes

### Issue 1: Search endpoint not working
**Problem:** Using `query` parameter instead of `q`  
**Solution:** Use `q` parameter
```bash
# ❌ Wrong
curl -X GET 'http://localhost:5002/api/search?query=apple'

# ✅ Correct
curl -X GET 'http://localhost:5002/api/search?q=apple'
```

### Issue 4: Ping endpoint returns 404
**Problem:** `/ping` endpoint was missing  
**Solution:** ✅ FIXED - Ping endpoint now available
```bash
# ✅ Now works
curl -X GET http://localhost:5002/ping
```

### Issue 5: Research endpoints failing with import errors
**Problem:** Missing 'src.research_prompts' module errors  
**Solution:** ✅ FIXED - Import paths corrected in ResearchManager
- `/api/research/progress` 
- `/api/research/prompts/available`
- `/api/research/prompts/estimate`
- `/api/research/structured/sessions`

### Issue 6: Research endpoint threading error
**Problem:** "signal only works in main thread" error  
**Solution:** ✅ FIXED - Removed signal-based timeout (scraper has built-in timeouts)

### Issue 7: Test discovery endpoint fails
**Problem:** Missing 'similarity_pipeline' attribute  
**Solution:** ✅ FIXED - Updated to use SimpleEnhancedDiscovery pattern

### Issue 2: Research endpoint failing
**Problem:** Incorrect JSON structure  
**Solution:** Wrap company data in `company` object
```bash
# ❌ Wrong
curl -X POST http://localhost:5002/api/research \
  -d '{"company_name": "Apple Inc"}'

# ✅ Correct
curl -X POST http://localhost:5002/api/research \
  -d '{"company": {"name": "Apple Inc", "website": "https://apple.com"}}'
```

### Issue 3: Research prompts estimate failing
**Problem:** Using `prompts` instead of `selected_prompts`  
**Solution:** Use correct field name
```bash
# ❌ Wrong
curl -X POST http://localhost:5002/api/research/prompts/estimate \
  -d '{"prompts": ["industry_analysis"]}'

# ✅ Correct
curl -X POST http://localhost:5002/api/research/prompts/estimate \
  -d '{"selected_prompts": ["industry_analysis"]}'
```

---

## 📋 Testing Script Corrections

The comprehensive testing script has been updated to use the correct parameters:

1. **Search endpoint:** Uses `q` parameter instead of `query`
2. **Research endpoint:** Uses proper nested `company` object structure
3. **Research estimate:** Uses `selected_prompts` instead of `prompts`
4. **Discovery endpoints:** Maintains correct structure

Run the updated test script with:
```bash
python3 tests/api_testing/comprehensive_endpoint_test.py
```