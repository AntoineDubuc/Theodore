#!/usr/bin/env python3
"""
GitHub API Test for Company Intelligence
Test GitHub's API for developer activity and company technology insights
"""

import os
import requests
import json
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env()

def test_github_api():
    """Test GitHub API for company intelligence gathering"""
    
    print("🔍 GITHUB API COMPANY INTELLIGENCE TEST")
    print("="*60)
    
    # GitHub API can be used without auth (60 requests/hour) or with auth (5000 requests/hour)
    github_token = os.getenv('GITHUB_TOKEN')
    
    if github_token:
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        print(f"🔑 Using authenticated access: {github_token[:8]}...")
        print("📊 Rate limit: 5,000 requests/hour")
    else:
        headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        print("🔓 Using unauthenticated access")
        print("📊 Rate limit: 60 requests/hour")
        print("💡 For better limits, add GITHUB_TOKEN to .env file")
    
    # Test companies and their known GitHub organizations
    test_companies = [
        {"name": "Procurify", "github_org": "procurify", "domain": "procurify.com"},
        {"name": "Stripe", "github_org": "stripe", "domain": "stripe.com"},
        {"name": "Shopify", "github_org": "shopify", "domain": "shopify.com"},
        {"name": "Slack", "github_org": "slackhq", "domain": "slack.com"},
        {"name": "Notion", "github_org": "makenotion", "domain": "notion.so"}
    ]
    
    results = []
    
    for company in test_companies:
        print(f"\n🏢 Testing: {company['name']} (@{company['github_org']})")
        print("-" * 40)
        
        company_data = test_company_github_presence(company, headers)
        results.append(company_data)
        
        # Rate limiting
        import time
        time.sleep(1)
    
    # Generate summary
    print(f"\n" + "="*60)
    print("📊 GITHUB API INTELLIGENCE SUMMARY")
    print("="*60)
    
    active_companies = [r for r in results if r.get('org_found')]
    tech_insights = {}
    
    for result in active_companies:
        company_name = result['company_name']
        print(f"\n🏢 {company_name}:")
        print(f"   📦 Public Repos: {result.get('public_repos', 0)}")
        print(f"   👥 Members: {result.get('members_count', 'Unknown')}")
        print(f"   📅 Created: {result.get('created_at', 'Unknown')}")
        print(f"   ⭐ Total Stars: {result.get('total_stars', 0)}")
        print(f"   🍴 Total Forks: {result.get('total_forks', 0)}")
        
        if result.get('top_languages'):
            print(f"   💻 Top Languages: {', '.join(result['top_languages'][:3])}")
            
        if result.get('activity_level'):
            print(f"   📈 Activity Level: {result['activity_level']}")
    
    print(f"\n🎯 GITHUB INTELLIGENCE VALUE FOR THEODORE:")
    print(f"   ✅ Company Tech Presence: {len(active_companies)}/{len(test_companies)} found")
    print(f"   ✅ Technology Stack Detection: Programming languages used")
    print(f"   ✅ Developer Activity: Commit frequency and project activity")
    print(f"   ✅ Open Source Commitment: Public repositories and contributions")
    print(f"   ✅ Company Size Indicator: GitHub organization size")
    
    return results

def test_company_github_presence(company, headers):
    """Test a specific company's GitHub presence"""
    
    result = {
        'company_name': company['name'],
        'github_org': company['github_org'],
        'domain': company['domain'],
        'org_found': False,
        'public_repos': 0,
        'total_stars': 0,
        'total_forks': 0,
        'top_languages': [],
        'activity_level': 'Unknown'
    }
    
    try:
        # Get organization info
        print("🔍 Checking organization...")
        org_response = requests.get(
            f"https://api.github.com/orgs/{company['github_org']}",
            headers=headers,
            timeout=10
        )
        
        if org_response.status_code == 200:
            org_data = org_response.json()
            result['org_found'] = True
            result['public_repos'] = org_data.get('public_repos', 0)
            result['created_at'] = org_data.get('created_at', '')
            result['members_count'] = org_data.get('public_members', 'Private')
            
            print(f"   ✅ Organization found")
            print(f"   📦 {result['public_repos']} public repositories")
            
            # Get repository details
            if result['public_repos'] > 0:
                repos_data = get_repo_intelligence(company['github_org'], headers)
                result.update(repos_data)
                
        elif org_response.status_code == 404:
            print(f"   ❌ Organization @{company['github_org']} not found")
        else:
            print(f"   ❓ API Error: {org_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    
    return result

def get_repo_intelligence(org_name, headers):
    """Get detailed repository intelligence for an organization"""
    
    repo_data = {
        'total_stars': 0,
        'total_forks': 0,
        'top_languages': [],
        'activity_level': 'Low'
    }
    
    try:
        # Get repositories (sorted by popularity)
        repos_response = requests.get(
            f"https://api.github.com/orgs/{org_name}/repos",
            params={'sort': 'updated', 'per_page': 10},
            headers=headers,
            timeout=10
        )
        
        if repos_response.status_code == 200:
            repos = repos_response.json()
            
            languages = {}
            recent_activity = 0
            
            for repo in repos:
                # Aggregate stats
                repo_data['total_stars'] += repo.get('stargazers_count', 0)
                repo_data['total_forks'] += repo.get('forks_count', 0)
                
                # Track languages
                language = repo.get('language')
                if language:
                    languages[language] = languages.get(language, 0) + 1
                
                # Check recent activity (last 30 days)
                updated_at = repo.get('updated_at', '')
                if updated_at:
                    from datetime import datetime, timedelta
                    try:
                        updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        if updated_date > datetime.now().replace(tzinfo=updated_date.tzinfo) - timedelta(days=30):
                            recent_activity += 1
                    except:
                        pass
            
            # Sort languages by usage
            sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)
            repo_data['top_languages'] = [lang for lang, count in sorted_languages[:5]]
            
            # Determine activity level
            if recent_activity >= 5:
                repo_data['activity_level'] = 'High'
            elif recent_activity >= 2:
                repo_data['activity_level'] = 'Medium'
            else:
                repo_data['activity_level'] = 'Low'
                
            print(f"   ⭐ {repo_data['total_stars']} total stars")
            print(f"   🍴 {repo_data['total_forks']} total forks")
            print(f"   📈 {recent_activity} repos updated in last 30 days")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Repo analysis failed: {e}")
    
    return repo_data

def show_github_integration_potential():
    """Show how GitHub API could enhance Theodore"""
    
    print(f"\n" + "="*60)
    print("🚀 GITHUB API + THEODORE INTEGRATION POTENTIAL")
    print("="*60)
    
    integration_benefits = {
        "Technology Stack Detection": "Identify programming languages and frameworks",
        "Developer Activity Level": "Gauge company's development velocity",
        "Open Source Presence": "Assess commitment to open source",
        "Team Size Estimation": "Estimate engineering team size",
        "Innovation Indicator": "Recent project activity and experimentation",
        "Technical Sophistication": "Code quality and project complexity",
        "Hiring Signal": "New repositories may indicate team growth",
        "Company Culture": "Open source vs. proprietary approach"
    }
    
    print("🎯 INTELLIGENCE CAPABILITIES:")
    for benefit, description in integration_benefits.items():
        print(f"   ✅ {benefit}: {description}")
    
    print(f"\n🔧 IMPLEMENTATION APPROACH:")
    print(f"   1. Organization Discovery: Find GitHub org from company domain")
    print(f"   2. Repository Analysis: Analyze public repos for tech stack")
    print(f"   3. Activity Tracking: Monitor development velocity")
    print(f"   4. Language Detection: Identify primary technologies")
    print(f"   5. Intelligence Integration: Add to Theodore company profiles")
    
    print(f"\n💰 COST ANALYSIS:")
    print(f"   🆓 Free Tier: 60 requests/hour (sufficient for testing)")
    print(f"   🔑 Authenticated: 5,000 requests/hour (excellent for production)")
    print(f"   💵 Cost: $0 (GitHub API is free)")

if __name__ == "__main__":
    try:
        results = test_github_api()
        show_github_integration_potential()
        
        print(f"\n🎉 GitHub API test completed!")
        print(f"💡 Add GITHUB_TOKEN to .env for better rate limits")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()