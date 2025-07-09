 Prompt
You are an expert business model analyst. Your task is to analyze a list of company websites by visiting their official websites and classify each one according to the two-step process below.
Please determine with 80% certainty whether the website noted in the list of URLs fits the definition. If not, list the classification as "not classified' in the output column
After analyzing all companies, provide the final output as a single CSV file w/";" as the delimiter; fields should be 
Company Name
URL    
Classification
Justification
Once you review this prompt, I will provide a list of companies for your analysis

Step 0: Exclude Competitors
Triage if the can by exclude from these definition of NIT Consulting Services: A

IT Consulting Services: A firm whose revenue is primarily derived from fees for providing human expertise, strategic advice, and implementation services related to a client's information technology systems.

Step 1: SaaS Identification
For each company, first, answer the following question based on the definition provided.
Is the company's primary business model Software-as-a-Service (SaaS)?
Definition of SaaS: A company whose primary product is a scalable software application that customers access online, typically through a recurring subscription. The core value is delivered through the technology itself, which customers use directly. Look for evidence on their website like a "Pricing" page with subscription tiers, discussions of "Platforms" or "Software," and language about "integrations," "APIs," or "product-led growth."
Step 2: Non-SaaS Classification
Only if the company is NOT a SaaS company, proceed to this step.
Choose the single best-fit category for the company from the list of Definitions for Non-SaaS Companies below. You will use this category name in the classification column and provide a brief justification in the justification column.
Definitions for Non-SaaS Companies
Advertising & Media Services: The primary offering is human-led professional services for marketing, advertising, and media campaigns. The business model is centered on generating revenue from retainers, project fees, and commissions for strategic and creative work delivered by its expert staff.
Biopharma R&D: The organization focuses on providing outsourced scientific services, such as managing clinical trials or performing laboratory analysis for drug developers. The value is delivered through contract-based research and the work of its scientific personnel.
Combo HW & SW: The product is an integrated unit where essential physical hardware and the software required to operate it are sold as a single, inseparable package. The business model relies on the sale of the physical appliance.
Education: An accredited institution (e.g., school, university) whose primary function is providing direct instruction and educational programs. The operational model is based on tuition, government funding, or grants.
Energy: The organization operates as a utility or provides direct services and physical infrastructure for energy production, management, or conservation. The core business involves managing tangible energy assets, not selling software.
Financial Services: A regulated institution that directly handles, manages, or lends financial assets as its primary activity. This includes banks, investment firms, and lenders whose revenue is generated from interest or fees on assets under management (AUM).
Healthcare Services: An organization that provides direct patient care, medical treatments, or administrative management services for clinical practices. The value is delivered through the hands-on services of healthcare professionals.
Industry Consulting Services: A specialized consulting firm that provides deep subject-matter expertise and strategic advice for a specific non-IT industry. The business model is based on fees for human-led, expert advisory services.
Insurance: A regulated entity that underwrites financial risk by creating, selling, and managing insurance policies. The operational model is based on collecting premiums to cover potential claims.
Logistics Services: The company's primary activity is the physical transportation, storage, and management of tangible goods or records. The core offering must be the physical movement and or storage of these items.
Manufacturing: The business model is centered on the fabrication and sale of physical goods or components. The primary source of revenue comes from the per-unit sale of the tangible products it creates.
Non-Profit:  one of many not-for-profit organizations in a variety of sectors ranging from public policy to research to charity to technology among many others
Retail: The company sells physical goods or provides in-person services directly to the public for personal use through online or brick-and-mortar storefronts.
Real Estate / Law Firms: The company manages real estate properties,  serves as a construction contractor for commercial and residential real estate,  or is a law firm composed of  attorneys and  legal  professionals delivering human Based Services
Sports: A professional sports franchise, league, or organization whose revenue is generated from sources tied to live events, including ticketing, media rights, sponsorships, and merchandise.
Travel & Leisure: The business provides in-person services and amenities related to tourism, hospitality, and recreation, with a model based on ticket sales, membership fees, or per-use charges.
Wholesale Distribution & Supply: The company acts as an intermediary, buying physical goods in bulk and reselling them to other businesses. The core business must be the handling and resale of physical goods.

3. SaaS Verticals
Once you have completed of steps 1 and 2 for triage of SaaS versus non-SaaS, take only companies that met the criteria for SaS and proceed with the classifications below to determine their "SaaS Vertical"
Use this category name in the new SaaS classification column and provide a brief justification in the justification column.
AdTech
AdTech SaaS platforms help advertisers, media companies, and marketers optimize advertising performance across digital channels. These platforms deliver value through automated ad placement, programmatic buying, creative optimization, audience measurement, and campaign analytics. Includes video platforms, podcast advertising, mobile ad tech, and broadcast media automation via cloud-based subscription services.
AssetManagement
SaaS platforms for Asset Management help organizations track, optimize, and manage both financial and physical assets throughout their lifecycle. They offer value through automated tracking of IT assets, intellectual property management, subscription optimization, technology transfer tools, and portfolio analysis for both investment firms and enterprise asset management via subscription-based access.
Billing
Billing SaaS solutions automate invoicing, subscription management, revenue recognition, and payment processing for businesses of all sizes. They provide scalable value through recurring access to billing engines, commission management, payment gateways, and financial workflow automation that integrate with accounting, CRM, and ERP systems.
Bio/Life Sciences
Bio/Life Sciences SaaS platforms provide specialized tools for pharmaceutical, biotech, and research organizations including clinical trial management, laboratory data systems, regulatory compliance, manufacturing process management, scientific collaboration platforms, and medical imaging workflows. They deliver value through compliance-ready, cloud-hosted software tailored for highly regulated life sciences environments.
CollabTech
CollabTech SaaS tools enable distributed teamwork through shared digital workspaces, real-time communication, project management, and workflow automation. These platforms drive productivity by providing seamless collaboration, document sharing, task management, and team coordination across remote and hybrid teams with subscription access.
Data/BI/Analytics
Data, BI, and Analytics SaaS platforms provide cloud-based tools for data collection, processing, visualization, and analysis across industries. They enable customers to derive actionable insights through real-time dashboards, predictive analytics, data warehousing, mobile app analytics, GPU-accelerated processing, and self-service business intelligence tools.
DevOps/CloudInfra
DevOps and Cloud Infrastructure SaaS platforms offer comprehensive tools for application deployment, infrastructure management, CI/CD pipelines, cloud security, monitoring, and container orchestration (including Kubernetes). They deliver value by improving development velocity, system reliability, and security for software development organizations, with expanded scope including domain registration, hosting, storage solutions, and cloud security platforms.
E-commerce & Retail
SaaS platforms for E-commerce & Retail support online and offline commerce through checkout optimization, inventory management, wholesale platforms, merchandising systems, store operations, and customer engagement tools. They provide value by streamlining retail operations, improving conversion rates, and enabling omnichannel experiences through scalable, cloud-based solutions.
EdTech
EdTech SaaS platforms facilitate digital learning, curriculum delivery, student engagement, and educational administration. These services provide value to educators, learners, and institutions through subscription-based interactive learning tools, learning management systems, student information systems, and educational content platforms.
Enertech
EnerTech SaaS solutions serve energy and utilities companies with tools for grid management, energy analytics, sustainability tracking, renewable energy optimization, and decarbonization planning. They deliver value by optimizing energy usage, enabling regulatory compliance, supporting clean energy initiatives, and providing operational insights through cloud-native platforms.
FinTech
FinTech SaaS platforms offer comprehensive digital financial services including payment processing, lending, trading platforms, regulatory compliance, risk management, merchant services, and specialized financial tools for various industries. They deliver value by providing scalable, secure, and compliant services that streamline financial operations for consumers, businesses, and financial institutions.
GovTech
GovTech SaaS platforms serve government agencies and public sector organizations with tools for digital services delivery, permitting systems, records management, public engagement, regulatory compliance, and administrative efficiency. They add value by improving transparency, accessibility, and operational efficiency through secure, subscription-based software services designed for public sector needs.
HRTech
HRTech SaaS platforms automate and optimize human resources processes including recruitment, applicant tracking, employee onboarding, payroll management, performance evaluation, benefits administration, and specialized talent marketplaces. They deliver value by reducing administrative overhead, improving employee experience, and enabling data-driven HR decisions via intuitive, cloud-based interfaces.
HealthTech
HealthTech SaaS solutions support clinical workflows, patient engagement, medical imaging, pharmacy management, healthcare data analytics, and care coordination. These platforms deliver value by enhancing healthcare delivery, ensuring compliance with medical regulations, improving patient outcomes, and streamlining healthcare operations through secure, scalable digital tools designed for healthcare environments.
Identity & Access Management (IAM)
IAM SaaS platforms manage user identities, authentication, access permissions, fraud prevention, and physical access control across digital and physical systems. They provide security and compliance value through centralized identity verification, access governance, threat detection, and subscription-based tools that reduce security risk while improving operational control and user experience.
InsureTech
InsureTech SaaS platforms streamline insurance industry processes including policy management, claims processing, underwriting automation, risk assessment, and customer engagement. They deliver value by increasing operational efficiency, reducing fraud, enhancing customer experience, and enabling data-driven insurance decisions through cloud-based automation and analytics tools.
LawTech
LawTech SaaS platforms provide digital tools for legal practice management including case management, legal research, compliance tracking, contract management, litigation support, and legal workflow automation. These platforms create value by automating legal processes, improving access to legal services, and enhancing efficiency for law firms and legal departments via subscription-based cloud software.
LeisureTech
LeisureTech SaaS solutions support businesses in recreation, hospitality, events, travel, and lifestyle services with booking systems, ticketing platforms, customer management, experience optimization, and operational tools. They provide value by enhancing customer engagement, streamlining operations, and improving revenue management for leisure and hospitality businesses via cloud-based tools.
Manufacturing/AgTech/IoT
SaaS platforms in Manufacturing, AgTech, and IoT offer tools for production optimization, equipment monitoring, maintenance management, precision agriculture, connected device management, and industrial automation via data integration and cloud platforms. They create value by enabling data-driven operations, predictive maintenance, quality control, and real-time visibility into physical assets and processes.
Martech & CRM
MarTech & CRM SaaS platforms help businesses attract, convert, and retain customers through marketing automation, sales intelligence, customer relationship management, revenue operations, creative workflow management, and customer experience optimization. These platforms deliver value by increasing marketing ROI, improving sales performance, and enhancing customer engagement via scalable cloud solutions.
MediaTech
MediaTech SaaS platforms support content creation, management, distribution, and monetization for media businesses including streaming services, digital asset management, content workflow automation, and media analytics. They deliver value through tools that enable scalable media operations, audience engagement, and revenue optimization via cloud-based media infrastructure.
PropTech
PropTech SaaS platforms digitize real estate operations including property listings, property management, tenant communication, real estate transactions, facilities management, and construction technology. They deliver value by increasing efficiency, transparency, and user experience in property-related services while enabling data-driven decision making in real estate operations.
Risk/Audit/Governance
SaaS platforms in Risk, Audit, and Governance provide comprehensive cybersecurity solutions, compliance automation, internal controls, risk assessments, threat detection, and governance frameworks. They create value by improving security posture, ensuring regulatory compliance, managing operational risk, and reducing manual oversight effort via secure, cloud-based security and compliance tools.
Social/Community/Non-Profit
These SaaS platforms support nonprofits, community organizations, and social impact initiatives with fundraising tools, volunteer management, donor engagement, community building, social networking, and mission-focused operational tools. They deliver value by enhancing social impact, improving operational efficiency, and enabling better community engagement through accessible cloud solutions.
Supply Chain & Logistics
Supply Chain & Logistics SaaS platforms provide comprehensive visibility, tracking, optimization, and coordination tools for goods movement, inventory management, procurement, vendor management, and logistics operations. They create value by reducing delays, optimizing costs, improving supply chain resilience, and enhancing coordination across complex logistics networks via hosted cloud services.
TranspoTech
TranspoTech SaaS platforms serve transportation and mobility companies with tools for fleet management, route optimization, mobility-as-a-service, transportation analytics, and logistics coordination. They add value by boosting operational efficiency, improving customer service, optimizing routes and fuel usage, and enabling new mobility business models through cloud-driven transportation solutions.



