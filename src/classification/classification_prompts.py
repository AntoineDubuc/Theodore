"""
Classification prompts for SaaS business model analysis
Based on the 59-category taxonomy from the feature requirements
"""

# Complete 59-category taxonomy
CLASSIFICATION_TAXONOMY = """
## SaaS (Software-as-a-Service)
**Definition:** The company's primary product is a scalable software application that customers access online via a recurring subscription. The core value is delivered through the technology itself. Evidence includes pricing tiers, mentions of platforms, APIs, and product-led growth.

### SaaS Verticals (Choose one if the company is SaaS)
- **AdTech:** Tools for optimizing advertising campaigns (e.g., targeted ad placement, analytics).
- **AssetManagement:** Platforms for investment tracking, portfolio analysis, and compliance.
- **Billing:** Solutions for automated invoicing, subscription management, and payment processing.
- **Bio/LS:** Software for clinical data management, lab automation, or R&D collaboration.
- **CollabTech:** Tools for remote teamwork, shared workspaces, and real-time communication.
- **Data/BI/Analytics:** Platforms for data aggregation, visualization, and business intelligence.
- **DevOps/CloudInfra:** Tools for application deployment, infrastructure management, and CI/CD pipelines.
- **E-commerce & Retail:** Platforms for building and managing online storefronts, inventory, and payments.
- **EdTech:** Software for digital learning, curriculum delivery, and student engagement.
- **Enertech:** Solutions for energy grid management, sustainability tracking, and resource optimization.
- **FinTech:** Digital tools for payments, lending, budgeting, or investment management.
- **GovTech:** Platforms for government agencies (e.g., permitting, records management, public services).
- **HRTech:** Software for recruitment, payroll, employee onboarding, and performance management.
- **HealthTech:** Solutions supporting clinical workflows, patient data, and healthcare analytics.
- **Identity & Access Management (IAM):** Platforms for managing user identities, authentication, and access.
- **InsureTech:** Software for policy management, claims processing, and underwriting.
- **LawTech:** Tools for case management, legal research, e-discovery, and compliance.
- **LeisureTech:** Booking, ticketing, and management systems for recreation or event businesses.
- **Manufacturing/AgTech/IoT:** Software for equipment monitoring, precision farming, or IoT device management.
- **Martech & CRM:** Platforms for marketing automation, customer relationship management (CRM), and sales.
- **MediaTech:** Tools for content creation, digital asset management, streaming, and monetization.
- **PropTech:** Software for real estate listings, property management, and tenant services.
- **Risk/Audit/Governance:** Platforms for automating compliance, internal controls, and risk assessments.
- **Social / Community / Non Profit:** Fundraising, volunteer management, and outreach tools for non-profits.
- **Supply Chain & Logistics:** Software for tracking, visibility, and optimization of supply chains.
- **TranspoTech:** Fleet management, route optimization, and mobility-as-a-service platforms.

## Non-SaaS Categories (Choose one if the company is NOT SaaS)
- **Advertising & Media Services:** Human-led professional services for marketing campaigns.
- **Biopharma R&D:** Outsourced scientific services (e.g., clinical trials, lab analysis).
- **Combo HW & SW:** An inseparable package of physical hardware and its operating software.
- **Education:** An accredited instructional institution (e.g., university, school).
- **Energy:** A utility or provider of physical energy infrastructure and services.
- **Financial Services:** A regulated institution that handles financial assets (e.g., bank, investment firm).
- **Healthcare Services:** Direct patient care or medical practice management.
- **Industry Consulting Services:** Expert advisory services for a specific non-IT industry.
- **Insurance:** A regulated entity that underwrites and sells insurance policies.
- **IT Consulting Services:** Human-led IT strategy, implementation, and advisory services.
- **Logistics Services:** Primary business is the physical transportation and storage of goods.
- **Manufacturing:** Fabrication and per-unit sale of physical goods.
- **Non-Profit:** A not-for-profit organization (charity, research institute, policy group).
- **Retail:** Direct-to-consumer sale of physical goods or in-person services.
- **Sports:** A professional sports franchise, league, or governing body.
- **Travel & Leisure:** Provider of in-person hospitality and tourism services.
- **Wholesale Distribution & Supply:** Buys goods in bulk to resell to other businesses.

## Special Category
- **Unclassified:** Website is inaccessible, lacks sufficient information, or is a holding company with no clear primary business.
"""

SAAS_CLASSIFICATION_PROMPT = """
You are an expert business model analyst. Your primary function is to accurately analyze and classify companies based on their publicly stated business model.

COMPANY DATA TO ANALYZE:
Company Name: {company_name}
Website: {website}
AI Summary: {ai_summary}
Products/Services: {products_services}
Value Proposition: {value_proposition}
Company Description: {company_description}
Industry: {industry}

CLASSIFICATION INSTRUCTIONS:
1. **Access and Analyze:** Review the provided company information, focusing on products/services, value proposition, and business model.
2. **Classify:** Choose the **single best-fit** classification from the taxonomy below.
   - First, evaluate if the company fits the primary definition of **SaaS (Software-as-a-Service)**.
   - If it is a SaaS company, select the most appropriate **SaaS Vertical**.
   - If it is NOT a SaaS company, select the most appropriate **Non-SaaS Category**.
3. **Handle Ambiguity:** If the information is insufficient or unclear, use "Unclassified" and explain why.

CLASSIFICATION TAXONOMY:
{taxonomy}

OUTPUT FORMAT (STRICT):
Classification: [exact category name from taxonomy]
Confidence: [decimal from 0.0 to 1.0]
Justification: [one sentence based on evidence from the company data]
Is_SaaS: [true or false]

EXAMPLES:
Classification: AdTech
Confidence: 0.85
Justification: Company provides advertising technology platforms with subscription pricing and API access for campaign optimization.
Is_SaaS: true

Classification: Manufacturing
Confidence: 0.92
Justification: Company manufactures and sells physical automotive parts through distributor networks.
Is_SaaS: false

Classification: Unclassified
Confidence: 0.0
Justification: Insufficient information provided to determine primary business model.
Is_SaaS: false

Now analyze the company and provide your classification:
"""

# Helper function for formatting the complete prompt
def get_classification_prompt(company_data) -> str:
    """Format the classification prompt with company data"""
    return SAAS_CLASSIFICATION_PROMPT.format(
        company_name=company_data.name,
        website=company_data.website,
        ai_summary=company_data.ai_summary or "No AI summary available",
        products_services=", ".join(company_data.products_services_offered) if company_data.products_services_offered else "No products/services listed",
        value_proposition=company_data.value_proposition or "No value proposition available",
        company_description=company_data.company_description or "No company description available",
        industry=company_data.industry or "Unknown industry",
        taxonomy=CLASSIFICATION_TAXONOMY
    )