#!/usr/bin/env python3
"""
Script to review what's stored in Pinecone and generate a markdown report
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models import CompanyIntelligenceConfig
from src.pinecone_client import PineconeClient

def main():
    """Generate Pinecone review report"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Reviewing Pinecone Database Contents...")
    
    # Configuration
    config = CompanyIntelligenceConfig()
    
    # Initialize Pinecone client
    try:
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT'),
            index_name=os.getenv('PINECONE_INDEX_NAME')
        )
        print("✅ Connected to Pinecone")
    except Exception as e:
        print(f"❌ Failed to connect to Pinecone: {e}")
        return
    
    # Get index statistics
    stats = pinecone_client.get_index_stats()
    
    # Fetch all vectors (limited approach for demo)
    # Note: In production, you'd want pagination for large datasets
    try:
        # Get some sample data by querying with a dummy vector
        dummy_vector = [0.0] * config.pinecone_dimension
        query_response = pinecone_client.index.query(
            vector=dummy_vector,
            top_k=100,  # Get up to 100 companies
            include_metadata=True,
            include_values=False
        )
        
        companies_data = []
        for match in query_response.matches:
            companies_data.append({
                'id': match.id,
                'metadata': match.metadata,
                'score': match.score
            })
        
        print(f"📊 Found {len(companies_data)} companies in database")
        
    except Exception as e:
        print(f"❌ Failed to query companies: {e}")
        return
    
    # Generate markdown report
    markdown_content = generate_markdown_report(stats, companies_data)
    
    # Save to file
    output_file = "pinecone_database_review.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"✅ Report saved to {output_file}")

def generate_markdown_report(stats, companies_data):
    """Generate markdown report of Pinecone contents"""
    
    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    markdown = f"""# Theodore Pinecone Database Review

**Generated:** {report_time}

## Database Statistics

| Metric | Value |
|--------|-------|
| Total Vectors | {stats.get('total_vectors', 'N/A')} |
| Vector Dimension | {stats.get('dimension', 'N/A')} |
| Index Fullness | {stats.get('index_fullness', 'N/A')} |
| Namespaces | {len(stats.get('namespaces', {}))} |

## Companies Overview

**Total Companies Found:** {len(companies_data)}

"""
    
    if not companies_data:
        markdown += "❌ No companies found in the database.\n"
        return markdown
    
    # Group companies by industry
    industries = {}
    for company in companies_data:
        metadata = company['metadata']
        industry = metadata.get('industry', 'unknown')
        if industry not in industries:
            industries[industry] = []
        industries[industry].append(company)
    
    markdown += f"## Companies by Industry\n\n"
    
    for industry, companies in industries.items():
        markdown += f"### {industry.title()} ({len(companies)} companies)\n\n"
        
        for company in companies:
            metadata = company['metadata']
            
            markdown += f"#### {metadata.get('company_name', 'Unknown Company')}\n\n"
            markdown += f"- **Website:** {metadata.get('website', 'N/A')}\n"
            markdown += f"- **Business Model:** {metadata.get('business_model', 'Unknown')}\n"
            markdown += f"- **Company Size:** {metadata.get('company_size', 'Unknown')}\n"
            markdown += f"- **Target Market:** {metadata.get('target_market', 'Unknown')}\n"
            
            # Technologies
            tech_stack = metadata.get('tech_stack', '')
            if tech_stack:
                techs = [tech.strip() for tech in tech_stack.split(',') if tech.strip()]
                if techs:
                    markdown += f"- **Technologies:** {', '.join(techs)}\n"
            
            # Services
            services = metadata.get('key_services', '')
            if services:
                services_list = [svc.strip() for svc in services.split(',') if svc.strip()]
                if services_list:
                    markdown += f"- **Key Services:** {', '.join(services_list[:3])}{'...' if len(services_list) > 3 else ''}\n"
            
            # Pain points
            pain_points = metadata.get('pain_points', '')
            if pain_points:
                pains_list = [pain.strip() for pain in pain_points.split(',') if pain.strip()]
                if pains_list:
                    markdown += f"- **Pain Points:** {', '.join(pains_list)}\n"
            
            # UI Features
            ui_features = []
            if metadata.get('has_chat_widget'):
                ui_features.append('Chat Widget')
            if metadata.get('has_forms'):
                ui_features.append('Lead Forms')
            
            if ui_features:
                markdown += f"- **UI Features:** {', '.join(ui_features)}\n"
            
            # Scrape info
            markdown += f"- **Scrape Status:** {metadata.get('scrape_status', 'Unknown')}\n"
            markdown += f"- **Created:** {metadata.get('created_at', 'Unknown')}\n"
            
            markdown += "\n---\n\n"
    
    # Summary statistics
    markdown += "## Summary Statistics\n\n"
    
    # Industry distribution
    markdown += "### Industry Distribution\n\n"
    markdown += "| Industry | Count | Percentage |\n"
    markdown += "|----------|-------|------------|\n"
    
    total_companies = len(companies_data)
    for industry, companies in sorted(industries.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(companies)
        percentage = (count / total_companies) * 100
        markdown += f"| {industry.title()} | {count} | {percentage:.1f}% |\n"
    
    # Technology popularity
    tech_counter = {}
    for company in companies_data:
        tech_stack = company['metadata'].get('tech_stack', '')
        if tech_stack:
            techs = [tech.strip().lower() for tech in tech_stack.split(',') if tech.strip()]
            for tech in techs:
                tech_counter[tech] = tech_counter.get(tech, 0) + 1
    
    if tech_counter:
        markdown += "\n### Most Common Technologies\n\n"
        markdown += "| Technology | Companies Using | Percentage |\n"
        markdown += "|------------|-----------------|------------|\n"
        
        sorted_techs = sorted(tech_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        for tech, count in sorted_techs:
            percentage = (count / total_companies) * 100
            markdown += f"| {tech.title()} | {count} | {percentage:.1f}% |\n"
    
    # Company size distribution
    size_counter = {}
    for company in companies_data:
        size = company['metadata'].get('company_size', 'unknown')
        size_counter[size] = size_counter.get(size, 0) + 1
    
    if size_counter:
        markdown += "\n### Company Size Distribution\n\n"
        markdown += "| Size | Count | Percentage |\n"
        markdown += "|------|-------|------------|\n"
        
        for size, count in sorted(size_counter.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_companies) * 100
            markdown += f"| {size.title()} | {count} | {percentage:.1f}% |\n"
    
    markdown += f"\n---\n\n*Report generated by Theodore Company Intelligence System*\n"
    
    return markdown

if __name__ == "__main__":
    main()