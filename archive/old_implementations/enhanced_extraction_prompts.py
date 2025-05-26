"""
Enhanced extraction prompts for comprehensive sales intelligence
Designed specifically for Theodore's company analysis goals
"""

# Enhanced extraction prompt for sales intelligence
SALES_INTELLIGENCE_PROMPT = """You are an expert sales intelligence analyst. Extract comprehensive business intelligence from this webpage that would be valuable for B2B sales prospecting and market analysis.

Extract and return the following information as valid JSON:
{
    "company_profile": {
        "company_name": "Official company name",
        "industry": "Primary industry/sector",
        "business_model": "B2B/B2C/SaaS/Marketplace/etc",
        "company_description": "Brief description of what they do",
        "value_proposition": "Main value proposition or tagline",
        "target_market": "Primary customer segments",
        "company_stage": "Startup/Growth/Enterprise/Public"
    },
    "business_metrics": {
        "employee_count": "Number of employees or range (e.g. 50-100)",
        "revenue_indicators": "Any revenue, ARR, or financial metrics mentioned",
        "funding_status": "Recent funding rounds, total raised, investors",
        "growth_signals": ["Recent hiring", "Office expansion", "New products", "Awards"],
        "market_position": "Market leader/challenger/niche player",
        "geographic_presence": "Locations, markets served"
    },
    "sales_intelligence": {
        "key_decision_makers": ["Name - Title - Department"],
        "organizational_structure": "Team size, departments mentioned",
        "technology_stack": ["Technologies used in operations"],
        "integration_partners": ["Technology partners", "Channel partners"],
        "competitive_advantages": ["Unique selling points", "Differentiators"],
        "recent_news": ["Product launches", "Partnerships", "Expansions"]
    },
    "sales_triggers": {
        "expansion_signals": ["New offices", "Hiring sprees", "Market expansion"],
        "technology_adoption": ["Digital transformation", "New tech implementations"],
        "leadership_changes": ["New executives", "Organizational changes"],
        "financial_events": ["Funding", "IPO", "Acquisitions"],
        "product_launches": ["New offerings", "Feature releases"]
    },
    "contact_intelligence": {
        "headquarters": "Main office location",
        "contact_methods": {
            "website": "Primary website",
            "email": "General contact email",
            "phone": "Phone number",
            "social_media": ["LinkedIn", "Twitter", "etc"]
        },
        "office_locations": ["All office locations mentioned"]
    },
    "competitive_landscape": {
        "competitors_mentioned": ["Direct competitors named"],
        "market_positioning": "How they position vs competition",
        "unique_differentiators": ["What sets them apart"],
        "target_customer_pain_points": ["Problems they solve"]
    }
}

IMPORTANT: Only include information that is clearly stated or strongly implied in the content. Use "unknown" for missing information. Focus on actionable sales intelligence that would help a sales team understand the company's business, growth trajectory, and potential needs.

Return only valid JSON, no other text.

Webpage content:
"""

# Specialized prompt for leadership/team pages
LEADERSHIP_INTELLIGENCE_PROMPT = """You are an expert at extracting organizational intelligence for sales prospecting. Analyze this leadership/team page to extract detailed information about key decision makers and organizational structure.

Extract and return the following as valid JSON:
{
    "leadership_team": [
        {
            "name": "Full name",
            "title": "Official job title",
            "department": "Department/Function (Sales, Engineering, Marketing, etc)",
            "seniority_level": "C-level/VP/Director/Manager",
            "background": "Previous experience or education if mentioned",
            "tenure": "How long at company if mentioned",
            "decision_making_power": "Budget/Technology/Strategic decisions",
            "contact_hints": "LinkedIn, email patterns, or contact info"
        }
    ],
    "organizational_insights": {
        "company_size_indicators": "Team size clues from number of leaders shown",
        "department_structure": ["Departments that exist based on leadership"],
        "growth_indicators": ["Recent hires", "New roles", "Expanding teams"],
        "company_culture": "Culture indicators from bios/descriptions",
        "hiring_signals": ["Open positions mentioned", "Growing teams"]
    },
    "sales_targeting": {
        "key_buyers": ["Names and titles of likely budget holders"],
        "technical_influencers": ["Engineering/IT decision makers"],
        "business_stakeholders": ["Business side decision makers"],
        "entry_points": ["Best contacts for initial outreach"]
    }
}

Only include information clearly present in the content. Return valid JSON only.

Leadership page content:
"""

# Specialized prompt for services/products pages
PRODUCT_INTELLIGENCE_PROMPT = """You are a competitive intelligence analyst. Extract detailed information about this company's products, services, and market positioning for sales intelligence purposes.

Extract and return as valid JSON:
{
    "product_portfolio": {
        "primary_offerings": ["Main products/services"],
        "service_categories": ["Types of services offered"],
        "target_use_cases": ["Problems solved", "Use cases addressed"],
        "pricing_models": "Pricing structure if mentioned",
        "product_maturity": "New/Established/Legacy products"
    },
    "market_intelligence": {
        "target_industries": ["Industries they serve"],
        "customer_segments": ["SMB/Mid-market/Enterprise"],
        "geographic_markets": ["Regions/countries served"],
        "vertical_specialization": ["Industry expertise areas"],
        "customer_examples": ["Customer case studies or names"]
    },
    "competitive_positioning": {
        "value_propositions": ["Key selling points"],
        "differentiators": ["What makes them unique"],
        "technology_advantages": ["Technical capabilities"],
        "market_approach": "How they go to market",
        "partnership_strategy": ["Technology/channel partners"]
    },
    "sales_opportunities": {
        "solution_gaps": ["Areas where they might need help"],
        "technology_needs": ["Potential technology requirements"],
        "scaling_challenges": ["Growth-related needs"],
        "integration_opportunities": ["Systems they might integrate with"],
        "expansion_signals": ["Growth areas or new markets"]
    }
}

Focus on actionable intelligence for sales targeting. Return valid JSON only.

Product/Services content:
"""

# Specialized prompt for news/press pages
NEWS_INTELLIGENCE_PROMPT = """Extract recent company developments and sales triggers from this news/press content.

Extract as valid JSON:
{
    "recent_developments": [
        {
            "date": "Date if available",
            "event_type": "Funding/Product Launch/Partnership/Hiring/Expansion",
            "description": "Brief description",
            "sales_relevance": "Why this matters for sales targeting"
        }
    ],
    "growth_signals": {
        "funding_events": ["Recent investments or funding rounds"],
        "product_launches": ["New products or features"],
        "market_expansion": ["New markets or geographies"],
        "team_growth": ["Hiring announcements or team expansions"],
        "partnerships": ["New partnerships or integrations"]
    },
    "sales_triggers": {
        "immediate_opportunities": ["Events suggesting immediate sales potential"],
        "timing_indicators": ["When they might be ready to buy"],
        "budget_signals": ["Signs they have budget for new initiatives"],
        "priority_areas": ["Areas they're investing in"]
    }
}

Return valid JSON only.

News content:
"""