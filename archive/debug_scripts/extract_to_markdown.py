#!/usr/bin/env python3
"""
Extract all Crawl4AI data and output to markdown file for review
"""

import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

from src.models import CompanyData, CompanyIntelligenceConfig
from src.enhanced_crawl4ai_scraper import EnhancedCrawl4AICompanyScraper
from src.pinecone_client import PineconeClient

logging.basicConfig(level=logging.WARNING)

async def extract_to_markdown():
    """Extract all data and output to markdown"""
    
    load_dotenv()
    
    config = CompanyIntelligenceConfig()
    company = CompanyData(name="Visterra Inc", website="https://visterrainc.com")
    scraper = EnhancedCrawl4AICompanyScraper(config)
    
    print("🚀 Extracting all Crawl4AI data for Pinecone storage...")
    
    # Run comprehensive extraction
    result = await scraper.scrape_company_comprehensive(company)
    
    # Get Pinecone storage format
    pinecone_client = PineconeClient(config)
    pinecone_metadata = pinecone_client._prepare_pinecone_metadata(result)
    complete_metadata = pinecone_client._prepare_complete_metadata(result)
    
    # Create markdown output
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    markdown_content = f"""# Crawl4AI Pinecone Storage Data

**Company:** {result.name}  
**Website:** {result.website}  
**Extraction Date:** {timestamp}  
**Pages Crawled:** {len(result.pages_crawled)} pages  
**Duration:** {result.crawl_duration:.1f} seconds  

## Pages Crawled

{chr(10).join(f"- {url}" for url in result.pages_crawled)}

## Pinecone Metadata (stored with vector)

```json
{pinecone_metadata}
```

## Complete Company Data (stored separately)

### Basic Information
- **Company Name:** {result.name}
- **Industry:** {result.industry}
- **Business Model:** {result.business_model}
- **Target Market:** {result.target_market}
- **Location:** {result.location}
- **Employee Count:** {result.employee_count_range}

### Company Description
{result.company_description or "Not available"}

### Leadership Team ({len(result.leadership_team) if result.leadership_team else 0} executives)
{chr(10).join(f"- {leader}" for leader in (result.leadership_team or [])) or "Not available"}

### Key Services ({len(result.key_services) if result.key_services else 0} services)
{chr(10).join(f"- {service}" for service in (result.key_services or [])) or "Not available"}

### Technology Stack ({len(result.tech_stack) if result.tech_stack else 0} technologies)
{chr(10).join(f"- {tech}" for tech in (result.tech_stack or [])) or "Not available"}

### Contact Information
{f"**Address:** {result.location}" if result.location else ""}
{chr(10).join(f"**{k.title()}:** {v}" for k, v in (result.contact_info or {}).items() if v) or "Not available"}

## Raw Extraction Stats

- **Total Pages:** {len(result.pages_crawled)}
- **Crawl Duration:** {result.crawl_duration:.1f} seconds
- **Status:** {result.scrape_status}
- **Content Length:** {len(result.raw_content) if result.raw_content else 0:,} characters

## What Gets Stored in Pinecone

### Vector Storage
- **Text for Embedding:** Company description + key services + industry
- **Metadata:** Company name, industry, business model, target market, company size

### Separate Storage  
- **Complete Company Data:** All extracted fields including full leadership team, services, tech stack
- **Contact Information:** Full contact details and office locations
- **Crawl Metadata:** Pages crawled, extraction timestamp, duration

This data enables:
- **Similarity Search:** Find similar companies by industry, services, target market
- **Sales Intelligence:** Complete leadership and contact information  
- **Market Analysis:** Business model, company size, growth indicators
"""

    # Save to markdown file
    output_file = "crawl4ai_pinecone_data.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"✅ Pinecone data extracted to: {output_file}")
    return output_file

if __name__ == "__main__":
    output_file = asyncio.run(extract_to_markdown())
    print(f"📄 Review the extracted data in: {output_file}")