"""
LLM prompts for extracting similarity metrics from company websites
"""

INDUSTRY_CLASSIFICATION_FROM_RESEARCH_PROMPT = """
Based on the comprehensive company research data provided below, determine what industry this company operates in. 
Use ALL the detailed information provided - not just the company name - to make an accurate classification.

If the research data clearly indicates the industry through products, services, partnerships, or certifications, provide that classification.
If the data is insufficient or unclear, respond with "Insufficient Data" rather than guessing.

COMPANY RESEARCH DATA:
======================

Company Name: {company_name}
Website: {website}

BUSINESS OVERVIEW:
Company Description: {company_description}
Value Proposition: {value_proposition}
Business Model: {business_model}
Target Market: {target_market}

PRODUCTS & SERVICES:
Key Services: {key_services}
Competitive Advantages: {competitive_advantages}
Pain Points They Address: {pain_points}

COMPANY DETAILS:
Location: {location}
Founded: {founding_year}
Company Size: {company_size}
Employee Count: {employee_count_range}
Funding Status: {funding_status}

TECHNOLOGY & OPERATIONS:
Technology Stack: {tech_stack}
Has Customer Support Chat: {has_chat_widget}
Has Lead Capture Forms: {has_forms}

MARKET PRESENCE:
Industry Certifications: {certifications}
Key Partnerships: {partnerships}
Awards & Recognition: {awards}
Leadership Team: {leadership_team}
Recent News/Updates: {recent_news}

ANALYSIS INSTRUCTIONS:
- Look for explicit industry indicators in services, partnerships, certifications
- Consider the target market and what problems they solve
- Pay attention to industry-specific terminology in descriptions
- Check if partnerships or certifications indicate specific industries
- Only classify if you have strong evidence from the research data
- If evidence is weak or contradictory, respond with "Insufficient Data"

Industry: [provide single industry category in plain English, or "Insufficient Data"]
"""

COMPANY_STAGE_PROMPT = """
Based on the website content provided, classify this company's stage as one of:
- startup: Early stage, small team (< 50 employees), recent founding, seed/series A funding
- growth: Scaling phase, hiring actively, series B/C funding, expanding market presence  
- enterprise: Established company, large team (200+ employees), market leader, mature operations

Look for indicators like:
- Team size mentions
- Funding announcements
- Job posting volume
- Market position language
- Company history/founding date

Website content:
{content}

Classification: [startup/growth/enterprise]
Confidence: [0.0-1.0]
Reasoning: [brief explanation]
"""

TECH_SOPHISTICATION_PROMPT = """
Based on the website content, classify the technical sophistication as:
- high: Developer-focused, API documentation, technical blog, complex integrations
- medium: Some technical features, basic integrations, technical support mentioned
- low: Simple setup, no-code emphasis, non-technical target audience

Look for indicators like:
- API documentation existence
- Developer tools/SDKs
- Technical job postings (engineers, DevOps, etc.)
- Integration complexity
- Technical language vs business language

Website content:
{content}

Classification: [high/medium/low]
Confidence: [0.0-1.0]
Reasoning: [brief explanation]
"""

BUSINESS_MODEL_PROMPT = """
Based on the website content, classify the business model as:
- saas: Software as a Service, subscription-based, cloud platform
- services: Consulting, agency, professional services
- marketplace: Two-sided platform connecting buyers/sellers
- ecommerce: Online retail, physical/digital products
- other: Other business model

Look for indicators like:
- Pricing models (subscription, one-time, commission)
- Service descriptions
- Customer segments
- Revenue streams

Website content:
{content}

Classification: [saas/services/marketplace/ecommerce/other]
Confidence: [0.0-1.0]
Reasoning: [brief explanation]
"""

DECISION_MAKER_PROMPT = """
Based on the website content and job postings, identify the primary decision maker type:
- technical: Engineering-led decisions, CTO/VP Eng as buyers, technical evaluation
- business: Business-led decisions, CEO/VP Business as buyers, ROI-focused evaluation  
- hybrid: Mixed technical and business evaluation, multiple stakeholders

Look for indicators like:
- Leadership team backgrounds
- Job posting patterns (eng vs business roles)
- Content focus (technical vs business benefits)
- Case study decision makers

Website content:
{content}

Classification: [technical/business/hybrid]
Confidence: [0.0-1.0]
Reasoning: [brief explanation]
"""

GEOGRAPHIC_SCOPE_PROMPT = """
Based on the website content, classify geographic scope as:
- local: Single city/region focus
- regional: Country or multi-country region (e.g., North America, Europe)
- global: Worldwide presence and operations

Look for indicators like:
- Office locations mentioned
- Customer case studies geography
- Language support
- Compliance mentions (GDPR, etc.)
- "Global" vs "Local" positioning

Website content:
{content}

Classification: [local/regional/global]
Confidence: [0.0-1.0]
Reasoning: [brief explanation]
"""

def extract_similarity_metrics(content: str, llm_client) -> dict:
    """Extract all similarity metrics from website content"""
    results = {}
    
    prompts = {
        'company_stage': COMPANY_STAGE_PROMPT,
        'tech_sophistication': TECH_SOPHISTICATION_PROMPT,
        'business_model_type': BUSINESS_MODEL_PROMPT,
        'decision_maker_type': DECISION_MAKER_PROMPT,
        'geographic_scope': GEOGRAPHIC_SCOPE_PROMPT
    }
    
    for metric, prompt in prompts.items():
        response = llm_client.generate_text(prompt.format(content=content))
        results[metric] = parse_llm_response(response)
        
    return results

def parse_llm_response(response: str) -> dict:
    """Parse LLM response into structured data"""
    lines = response.strip().split('\n')
    result = {}
    
    for line in lines:
        if line.startswith('Classification:'):
            result['value'] = line.split(':')[1].strip()
        elif line.startswith('Confidence:'):
            try:
                result['confidence'] = float(line.split(':')[1].strip())
            except:
                result['confidence'] = 0.5
        elif line.startswith('Reasoning:'):
            result['reasoning'] = line.split(':')[1].strip()
            
    return result