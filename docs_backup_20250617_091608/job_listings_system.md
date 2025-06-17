# Job Listings Analysis System

## 🎯 Overview

Theodore's intelligent job listings analysis system provides comprehensive hiring insights through automated career page discovery, LLM-guided navigation, and **REAL Google search** integration. The system transforms traditional "404" or "not found" experiences into actual career page discoveries and job search guidance.

## 🧠 Core Architecture

### Multi-Step Discovery Process

```python
class JobListingsCrawler:
    """
    6-Step intelligent job listings discovery:
    1. Homepage Link Extraction - Crawl main page for all same-domain links
    2. LLM Career Page Selection - AI identifies most likely career page
    3. Career Page Analysis - Crawl and analyze career page content
    4. Job Listing Detection - Search for obvious job listings on career page
    5. Deep Link Analysis - If needed, find specific job listing pages
    6. REAL Google Search - Perform actual Google searches to discover career pages
    """
```

## 🔄 Processing Flow

### Step 1: Homepage Analysis
```python
def _crawl_main_page_links(self, url: str) -> List[str]:
    """
    - Extracts all same-domain links from company homepage
    - Filters to same domain to avoid external redirects
    - Limits to 50 links for LLM processing efficiency
    - Returns clean, absolute URLs for analysis
    """
```

### Step 2: Smart Early Detection
```python
# Before sending to LLM, check for obvious career keywords
career_keywords = ['career', 'job', 'work', 'hiring', 'join', 'team', 'employment', 'openings', 'opportunities']

if not obvious_career_links:
    # Skip expensive LLM processing, go straight to Google search fallback
    return google_search_fallback(company_name)
```

### Step 3: LLM-Guided Selection
```python
prompt = f"""
Analyze these links from {company_name}'s website and select the ONE link 
most likely to lead to a careers/jobs page.

Instructions:
- Look for URLs containing: careers, jobs, work, employment, join, team, hiring, opportunities
- Choose the MOST LIKELY link that would lead to their careers/jobs page
- Return ONLY the complete URL, nothing else
- If no career-related link exists, return exactly: NONE
"""
```

### Steps 4-5: Career Page Deep Analysis
- Crawl identified career page for job listings
- If no listings found, use LLM to identify specific job listing links
- Crawl those specific pages for actual job postings

### Step 6: REAL Google Search Integration

Performs actual Google searches to discover career pages:

```python
def _perform_real_google_search(self, company_name: str) -> Dict[str, Any]:
    """
    REAL Google search implementation:
    - Searches "MSI careers", "MSI jobs", "MSI hiring"
    - Uses Google Custom Search API or SerpAPI
    - Discovers URLs like https://ca.msi.com/about/careers
    - Crawls discovered pages for actual job listings
    - Returns specific career URLs and real job data
    """
```

**Google Search Methods:**
1. **Google Custom Search API** (recommended)
2. **SerpAPI** (alternative) 
3. **Direct Google search** (fallback, may be blocked)

## 🔧 Technical Implementation

### Dual AI Provider Support

```python
class JobListingsCrawler:
    def __init__(self, bedrock_client=None, openai_client=None):
        # Use OpenAI as primary, Bedrock as fallback
        if openai_client:
            self.llm_client = openai_client
            logger.info("🧠 Using OpenAI for LLM analysis")
        elif bedrock_client:
            self.llm_client = bedrock_client
            logger.info("🧠 Using Bedrock for LLM analysis")
        else:
            raise ValueError("Either OpenAI or Bedrock client must be provided")
```

**Why OpenAI Primary?**
- More reliable for job listings analysis
- Faster response times for interactive features
- Better performance with career page link selection
- Easier development/testing setup

### Integration with Research Pipeline

```python
# In simple_enhanced_discovery.py
def _execute_job_listings_research(self, company_name: str, company_website: str):
    """
    Integrates job listings analysis into comprehensive company research:
    1. Try OpenAI client first
    2. Fallback to Bedrock if OpenAI unavailable
    3. Execute intelligent crawling
    4. Return structured job listings data
    """
```

## 📊 Output Formats

### Successful Discovery
```json
{
  "job_listings": "Yes - 12 open positions",
  "details": {
    "positions": ["Software Engineer", "Product Manager", "Sales Director"],
    "evidence": ["Apply now buttons found", "12 job titles listed"],
    "source_analysis": "Clear job listings section with application links"
  },
  "found_jobs": true,
  "source": "career_page_content"
}
```

### Enhanced Fallback Guidance
```json
{
  "job_listings": "Try: LinkedIn, their careers page, AngelList | Direct link: https://stripe.com/jobs",
  "details": {
    "typical_roles": ["Software Engineer", "Product Manager", "Sales"],
    "best_job_sites": ["LinkedIn", "their careers page", "AngelList"],
    "career_page_url": "https://stripe.com/jobs",
    "search_tips": "Use keywords like 'Stripe' and 'payments' to narrow down relevant job listings.",
    "company_info": "Stripe is known for hiring top talent across various technical and business roles.",
    "hiring_status": "Likely active"
  },
  "source": "google_search_direct",
  "reason": "No career links found on homepage"
}
```

## 🎯 Key Features

### 1. Intelligent Early Fallback
- Detects when homepage has no career links
- Skips expensive LLM processing for impossible cases
- Immediately provides Google search guidance

### 2. Progressive Enhancement
- Works with basic link detection
- Enhanced by LLM guidance when possible
- Always provides useful output regardless of success/failure

### 3. Actionable Results
- Direct career page URLs when available
- Platform-specific job site recommendations
- Company-specific search strategies
- Role type guidance based on company analysis

### 4. Cost Optimization
- OpenAI for job listings (faster, more reliable)
- Bedrock for other analysis tasks (cost-effective)
- Early detection prevents unnecessary API calls

## 📋 Configuration

### Environment Variables
```bash
# Primary AI provider for job listings
OPENAI_API_KEY=sk-your-openai-key

# Fallback AI provider
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
BEDROCK_ANALYSIS_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
```

### Usage in Research Pipeline
```python
# Automatic integration in enhanced discovery
from src.simple_enhanced_discovery import SimpleEnhancedDiscovery

discovery = SimpleEnhancedDiscovery(bedrock_client, pinecone_client, scraper)
result = discovery.research_company_on_demand({
    "name": "Stripe",
    "website": "https://stripe.com"
})

# Job listings data available in result
job_info = result.get('job_listings', 'Not available')
job_details = result.get('job_listings_details', {})
```

## 🔍 Monitoring & Debugging

### Comprehensive Logging
```python
logger.info(f"🚀 Starting job listings crawl for {company_name} at {website}")
logger.info(f"✅ STEP 1 SUCCESS: Found {len(main_links)} links on main page")
logger.warning(f"⚠️ No obvious career links found in {len(main_links)} main page links")
logger.info(f"🌐 SKIP TO STEP 6: Using Google search since no career links found on homepage")
```

### Error Handling
- Network timeouts gracefully handled
- LLM API failures fall back to basic guidance
- Malformed websites handled with safe defaults
- All errors logged with context for debugging

## 🚀 Performance Characteristics

### Typical Processing Times
- **Homepage Analysis**: 2-5 seconds
- **LLM Career Page Selection**: 3-8 seconds
- **Career Page Crawling**: 2-4 seconds
- **Google Search Fallback**: 2-5 seconds
- **Total (successful)**: 15-25 seconds
- **Total (fallback)**: 5-10 seconds

### Cost Analysis
- **OpenAI GPT-3.5-turbo**: ~$0.002 per job listings analysis
- **AWS Bedrock Claude**: ~$0.003 per analysis (fallback)
- **Total per company**: $0.002-0.003 for job listings component

## 🔮 Future Enhancements

### Planned Improvements
1. **Real Job Board Integration**: Direct API connections to LinkedIn, Indeed
2. **Historical Hiring Tracking**: Monitor job posting changes over time
3. **Salary Range Analysis**: Extract compensation information when available
4. **Application Process Automation**: Guide users through application workflows

### Technical Roadmap
- **Caching Layer**: Cache career page analyses to reduce API calls
- **Batch Processing**: Analyze multiple companies' job listings in parallel
- **Machine Learning**: Learn from successful/failed career page discoveries
- **Custom Extractors**: Company-specific job listing parsing patterns

---

*The job listings analysis system transforms traditional web scraping challenges into opportunities for providing valuable, actionable guidance to users seeking employment opportunities.*