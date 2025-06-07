# Raw Pinecone Data Extract

**Generated:** 2025-06-06 16:54:15  
**Total Records:** 3

## Company 1: Anthropic

**Vector ID:** `b1486b56-80a4-41f8-bfc4-a31389837a15`  
**Similarity Score:** 0.000000  
**Embedding Dimensions:** 1536  
**Embedding Sample (first 10):** [0.8555, 0.1348, 0.1279, -0.2930, 0.3184, 0.1855, -0.0854, 0.0007, -0.3105, -0.2168...]  

### Metadata Fields:

- **Business Model:** B2B and B2C
- **Business Model Type:** saas
- **Company Name:** Anthropic
- **Company Size:** enterprise
- **Company Stage:** enterprise
- **Decision Maker Type:** technical
- **Geographic Scope:** global
- **Industry:** artificial intelligence
- **Target Market:** developers, businesses, researchers, and general consumers seeking AI assistance
- **Tech Sophistication:** high
- **Website:** https://anthropic.com

---

## Company 2: OpenAI

**Vector ID:** `0a72575b-100b-4b26-9b7c-5505dbccb3f9`  
**Similarity Score:** 0.000000  
**Embedding Dimensions:** 1536  
**Embedding Sample (first 10):** [0.3164, 0.1846, 0.1445, -0.0996, 0.2910, -0.0282, 0.0449, 0.0006, -0.1855, -0.1797...]  

### Metadata Fields:

- **Business Model:** B2B
- **Business Model Type:** saas
- **Company Name:** OpenAI
- **Company Size:** enterprise
- **Company Stage:** Unknown
- **Decision Maker Type:** Unknown
- **Geographic Scope:** global
- **Industry:** artificial intelligence
- **Target Market:** businesses and enterprises seeking AI integration
- **Tech Sophistication:** high
- **Website:** https://openai.com

---

## Company 3: Cloud Geometry

**Vector ID:** `46260cac-dad5-4beb-b7e7-99ae79275803`  
**Similarity Score:** 0.000000  
**Embedding Dimensions:** 1536  
**Embedding Sample (first 10):** [0.4902, 0.0967, 0.3496, 0.0079, 0.0016, 0.0439, -0.0591, 0.0007, -0.4277, 0.0603...]  

### Metadata Fields:

- **Business Model:** B2B
- **Business Model Type:** other
- **Company Name:** Cloud Geometry
- **Company Size:** SMB
- **Company Stage:** [unable to determine]
- **Decision Maker Type:** Unknown
- **Geographic Scope:** Unknown
- **Industry:** cloud consulting
- **Target Market:** mid-market and enterprise companies seeking cloud transformation
- **Tech Sophistication:** Unknown
- **Website:** https://cloudgeometry.io

---

## Technical Details

### Vector Storage Information
- **Vector Dimension:** 1536 (Amazon Titan Embeddings)
- **Distance Metric:** Cosine Similarity
- **Storage Format:** Pinecone Serverless (AWS us-west-2)
- **Metadata Fields:** Full company intelligence from Crawl4AI

### Available Metadata Fields (11 total):
- `business_model`
- `business_model_type`
- `company_name`
- `company_size`
- `company_stage`
- `decision_maker_type`
- `geographic_scope`
- `industry`
- `target_market`
- `tech_sophistication`
- `website`

### Data Sources
- **Web Scraping:** Crawl4AI multi-page extraction
- **AI Analysis:** AWS Bedrock (planned)
- **Embeddings:** Amazon Titan Text Embeddings
- **Pages Crawled:** Homepage, About, Services, Products, Team, Contact, etc.
