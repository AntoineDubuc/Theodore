"""
David's Business Model Framework Prompts
Structured business model description following exact framework requirements
"""

from typing import Dict, Any

# David's Business Model Framework Classification Prompt
BUSINESS_MODEL_FRAMEWORK_PROMPT = """
Based on your comprehensive company analysis, create a business model description following this exact framework:

**Required Structure:**
[Primary Model Type] ([Brief Value Mechanism Description])

**Primary Model Type - Choose ONE from these 11 options:**
- SaaS - Software as a Service/subscription-based software
- Product Sales - One-time hardware/software product sales  
- Hardware-enabled SaaS - Hardware + recurring software/service fees
- Manufacturing - Mass production and supply contracts
- Enterprise Software - Licensed platforms for large organizations
- Technology Licensing - IP/patent licensing to other companies
- Consulting Services - Professional expertise and advisory services
- Managed Services - Ongoing operational support and management
- Project-based Services - Contract-based project delivery
- Transaction-based - Fees per transaction/usage
- Subscription-based - Recurring access fees
- Marketplace/Platform - Commission on transactions between parties

**Value Mechanism Description - Explain in parentheses HOW the company monetizes:**
Must include these four elements:
- **WHO** pays (customer type: enterprises, consumers, SMBs, government, etc.)
- **WHAT** they pay for (specific product/service)
- **HOW** pricing works (per-user, per-transaction, fixed fee, monthly subscription, etc.)
- **WHY** customers pay (value received: efficiency gains, cost savings, new capabilities, etc.)

**Quality Requirements:**
- Concise: 1-2 sentences maximum
- Specific: Include concrete details about pricing and value where available
- Customer-centric: Focus on customer perspective and outcomes
- Business-viable: Explain how the model sustains the business

**Company Analysis Data:**
Company Name: {company_name}
Industry: {industry}
Business Model: {business_model}
Company Description: {company_description}
Value Proposition: {value_proposition}
Target Market: {target_market}
Products/Services: {products_services_offered}
Key Services: {key_services}
Competitive Advantages: {competitive_advantages}
AI Summary: {ai_summary}

**Generate ONLY the business model description following the exact framework format above. Do not include explanations or additional text.**
"""

def create_framework_prompt(company_data: Any) -> str:
    """Create framework prompt with company data"""
    
    # Extract relevant fields with fallbacks
    company_name = getattr(company_data, 'name', 'Unknown')
    industry = getattr(company_data, 'industry', 'Unknown') or 'Unknown'
    business_model = getattr(company_data, 'business_model', 'Unknown') or 'Unknown'
    company_description = getattr(company_data, 'company_description', 'N/A') or 'N/A'
    value_proposition = getattr(company_data, 'value_proposition', 'N/A') or 'N/A'
    target_market = getattr(company_data, 'target_market', 'N/A') or 'N/A'
    products_services = getattr(company_data, 'products_services_offered', 'N/A') or 'N/A'
    key_services = ', '.join(getattr(company_data, 'key_services', [])) or 'N/A'
    competitive_advantages = ', '.join(getattr(company_data, 'competitive_advantages', [])) or 'N/A'
    ai_summary = getattr(company_data, 'ai_summary', 'N/A') or 'N/A'
    
    return BUSINESS_MODEL_FRAMEWORK_PROMPT.format(
        company_name=company_name,
        industry=industry,
        business_model=business_model,
        company_description=company_description,
        value_proposition=value_proposition,
        target_market=target_market,
        products_services_offered=products_services,
        key_services=key_services,
        competitive_advantages=competitive_advantages,
        ai_summary=ai_summary
    )

def validate_framework_output(output: str) -> Dict[str, Any]:
    """Validate framework output against David's requirements"""
    
    if not output or not isinstance(output, str):
        return {
            "valid": False,
            "errors": ["No output provided"],
            "suggestions": ["Generate framework output"]
        }
    
    output = output.strip()
    errors = []
    warnings = []
    
    # Check format: [Primary Model Type] ([Value Mechanism])
    if not ("(" in output and ")" in output):
        errors.append("Missing parentheses structure")
    
    # Check if starts with valid primary model type
    valid_types = [
        "SaaS", "Product Sales", "Hardware-enabled SaaS", "Manufacturing", 
        "Enterprise Software", "Technology Licensing", "Consulting Services", 
        "Managed Services", "Project-based Services", "Transaction-based", 
        "Subscription-based", "Marketplace/Platform"
    ]
    
    starts_with_valid_type = any(output.startswith(t) for t in valid_types)
    if not starts_with_valid_type:
        errors.append("Does not start with valid Primary Model Type")
    
    # Check length (1-2 sentences, roughly < 60 words for flexibility)
    word_count = len(output.split())
    if word_count > 60:
        warnings.append(f"May be too long ({word_count} words, recommend < 60)")
    
    # Check for key elements (WHO, WHAT, HOW, WHY indicators)
    elements_found = {}
    
    # WHO indicators (customer types)
    who_terms = ["businesses", "companies", "customers", "enterprises", "consumers", 
                 "organizations", "users", "clients", "teams", "professionals"]
    elements_found["who_pays"] = any(term in output.lower() for term in who_terms)
    
    # WHAT indicators (products/services)
    what_terms = ["platform", "software", "service", "infrastructure", "solution", 
                  "product", "system", "tool", "application", "technology"]
    elements_found["what_pay_for"] = any(term in output.lower() for term in what_terms)
    
    # HOW indicators (pricing models)
    how_terms = ["fee", "subscription", "per-", "monthly", "annual", "transaction", 
                 "commission", "license", "pricing", "cost", "pay"]
    elements_found["how_pricing"] = any(term in output.lower() for term in how_terms)
    
    # WHY indicators (value propositions)
    why_terms = ["enabling", "providing", "delivering", "improving", "reducing", 
                 "automating", "simplifying", "optimizing", "managing", "without"]
    elements_found["why_value"] = any(term in output.lower() for term in why_terms)
    
    # Check if all elements are present
    missing_elements = [k for k, v in elements_found.items() if not v]
    if missing_elements:
        warnings.append(f"May be missing elements: {', '.join(missing_elements)}")
    
    # Overall validation
    is_valid = len(errors) == 0
    quality_score = sum(elements_found.values()) / len(elements_found.values())
    
    return {
        "valid": is_valid,
        "quality_score": quality_score,
        "word_count": word_count,
        "errors": errors,
        "warnings": warnings,
        "elements_found": elements_found,
        "formatted_output": output
    }

# Example framework outputs for reference
EXAMPLE_FRAMEWORK_OUTPUTS = {
    "stripe": "Transaction-based (online businesses pay per-transaction fees typically 2.9% + 30¢ for payment processing infrastructure that handles credit cards, international payments, and fraud prevention, enabling companies to accept payments without building complex payment systems)",
    
    "shopify": "SaaS (e-commerce businesses pay monthly subscription fees ranging from $29-$299+ for hosted online store platform with payment processing, inventory management, and marketing tools, generating recurring revenue as merchants grow their sales volume)",
    
    "salesforce": "Enterprise Software (large organizations pay per-user monthly licensing fees starting at $25/user for cloud-based CRM platform that manages sales pipelines, customer relationships, and business analytics, reducing manual sales processes)",
    
    "uber": "Marketplace/Platform (riders pay per-trip fees while drivers receive 70-80% commission for on-demand transportation matching service that connects supply and demand, with Uber taking 20-30% commission per ride)",
    
    "tesla": "Manufacturing (consumers and businesses purchase electric vehicles at fixed unit prices ranging from $35K-$130K+ for sustainable transportation with advanced autonomous features, supported by recurring service and charging network revenue)"
}