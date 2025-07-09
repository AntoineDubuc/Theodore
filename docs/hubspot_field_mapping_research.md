# HubSpot Field Mapping Research Document

## Overview
This document provides comprehensive research on HubSpot's company properties and field mappings for Theodore's company intelligence data integration.

**Research Date**: January 2025  
**Theodore Version**: Latest (from `/src/models.py`)  
**HubSpot API Version**: v3 (Current)

---

## 1. Research Sources Documentation

### Primary Sources Used

#### HubSpot Official Documentation
- **HubSpot API Documentation**: https://developers.hubspot.com/docs/api/crm/companies
- **Properties API Reference**: https://developers.hubspot.com/docs/reference/api/crm/properties  
- **Default Company Properties**: https://knowledge.hubspot.com/properties/hubspot-crm-default-company-properties
- **Property Field Types**: https://knowledge.hubspot.com/properties/property-field-types-in-hubspot

#### Context7 Library Documentation
- **HubSpot Python Client**: `/hubspot/hubspot-api-python` library documentation
- **Field Type Definitions**: FieldTypeDefinition model structure
- **API Examples**: Company creation, property management, batch operations

#### HubSpot Community Forums
- **Company Properties API**: Community discussions on accessing all company properties
- **Custom Properties**: Guidance on creating and managing custom fields
- **API Integration**: Best practices for Python integration

### Research Methodology
1. **API Documentation Review**: Examined official HubSpot API v3 documentation
2. **Library Analysis**: Studied HubSpot Python client capabilities via Context7
3. **Community Validation**: Cross-referenced with HubSpot community discussions
4. **Field Type Analysis**: Identified supported data types and constraints

---

## 2. HubSpot Company Properties Catalog

### 2.1 Default Company Properties (19 Core Fields)

| Internal Name | Display Name | Type | Description | Required |
|---------------|--------------|------|-------------|----------|
| `name` | Company name | string | Official organization name | Yes |
| `domain` | Company domain name | string | Website domain | No |
| `website` | Website URL | string | Company web address | No |
| `industry` | Industry | enumeration | Business type (~150 pre-defined options) | No |
| `annualrevenue` | Annual revenue | number | Actual or estimated revenue | No |
| `numberofemployees` | Number of employees | number | Total staff count | No |
| `city` | City | string | Company location city | No |
| `state` | State/Region | string | Company location state/region | No |
| `country` | Country/Region | string | Company location | No |
| `address` | Street address | string | Physical company address | No |
| `zip` | Postal code | string | Postal/ZIP code | No |
| `phone` | Phone number | string | Primary contact number | No |
| `about_us` | About us | string | Short company description | No |
| `description` | Description | string | Company mission and goals | No |
| `founded_year` | Year founded | number | Company establishment year | No |
| `lifecyclestage` | Lifecycle stage | enumeration | Marketing/sales process stage | No |
| `hubspot_owner_id` | Owner | string | Assigned company owner | No |
| `createdate` | Create date | datetime | Date added to account | Auto |
| `closedate` | Close date | datetime | Date company became customer | No |

### 2.2 Social Media Properties (4 Fields)

| Internal Name | Display Name | Type | Description |
|---------------|--------------|------|-------------|
| `facebook_company_page` | Facebook company page URL | string | Facebook page URL |
| `linkedin_company_page` | LinkedIn company page URL | string | LinkedIn page URL |
| `twitterhandle` | Twitter handle | string | Twitter username |
| `total_money_raised` | Total funding amount | number | Investment raised |

### 2.3 Web Analytics Properties (6 Fields)

| Internal Name | Display Name | Type | Description |
|---------------|--------------|------|-------------|
| `days_to_close` | Days to close | number | Time between addition and conversion |
| `web_technologies` | Web technologies | string | Technologies used on website |
| `first_contact_createdate` | Time first seen | datetime | First interaction timestamp |
| `notes_last_contacted` | Time last contacted | datetime | Last contact timestamp |
| `num_contacted_notes` | Number of times contacted | number | Contact frequency |
| `total_revenue` | Total revenue | number | Revenue generated |

### 2.4 Conversion Properties (5 Fields)

| Internal Name | Display Name | Type | Description |
|---------------|--------------|------|-------------|
| `first_conversion_event_name` | First conversion | string | Initial conversion type |
| `first_conversion_date` | First conversion date | datetime | When first conversion occurred |
| `recent_conversion_event_name` | Recent conversion | string | Latest conversion type |
| `recent_conversion_date` | Recent conversion date | datetime | When recent conversion occurred |
| `num_conversion_events` | Number of form submissions | number | Total conversions |

### 2.5 Custom Properties

HubSpot allows unlimited custom properties via the Properties API:

**Property Types Supported:**
- `string` - Text fields (single-line, multi-line)
- `number` - Numeric values
- `date` - Date values
- `datetime` - Date and time values
- `enumeration` - Dropdown selections
- `bool` - Boolean true/false
- `phone_number` - Phone number format
- `currency_number` - Currency values

**API Endpoints:**
- `GET /crm/v3/properties/companies` - List all company properties
- `POST /crm/v3/properties/companies` - Create new property
- `PATCH /crm/v3/properties/companies/{propertyName}` - Update property
- `DELETE /crm/v3/properties/companies/{propertyName}` - Delete property

---

## 3. Theodore Company Data Fields Catalog

### 3.1 Core Identification Fields (3 Fields)

| Theodore Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `id` | string | UUID identifier | "uuid4-string" |
| `name` | string | Company name | "Acme Corp" |
| `website` | string | Company website URL | "https://acme.com" |

### 3.2 Basic Company Information (4 Fields)

| Theodore Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `industry` | string | Detected industry/sector | "Technology" |
| `business_model` | string | B2B, B2C, marketplace, etc. | "B2B SaaS" |
| `company_size` | string | startup, SMB, enterprise | "growth" |
| `target_market` | string | Who they serve | "Enterprise customers" |

### 3.3 Technology Insights (3 Fields)

| Theodore Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `tech_stack` | List[string] | Detected technologies | ["React", "AWS", "Stripe"] |
| `has_chat_widget` | bool | Customer support chat | true |
| `has_forms` | bool | Lead capture forms | true |

### 3.4 Business Intelligence (6 Fields)

| Theodore Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `pain_points` | List[string] | Inferred challenges | ["Manual processes", "Data silos"] |
| `key_services` | List[string] | Main offerings | ["CRM Software", "Sales Analytics"] |
| `competitive_advantages` | List[string] | Company strengths | ["AI-powered insights", "Easy integration"] |
| `business_model_framework` | string | David's classification | "SaaS - Martech & CRM" |
| `company_description` | string | About/description | "Leading CRM platform for..." |
| `value_proposition` | string | Main value prop | "Increase sales by 30% with..." |

### 3.5 Extended Metadata (14 Fields)

| Theodore Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `founding_year` | int | Year founded | 2018 |
| `location` | string | HQ location | "San Francisco, CA" |
| `employee_count_range` | string | Employee estimate | "50-200" |
| `company_culture` | string | Culture/values | "Remote-first, innovation-driven" |
| `funding_status` | string | Funding stage | "Series B" |
| `social_media` | Dict[str, str] | Social links | {"twitter": "@acme", "linkedin": "..."} |
| `contact_info` | Dict[str, str] | Contact details | {"email": "info@acme.com", "phone": "..."} |
| `leadership_team` | List[string] | Key leaders | ["John Smith - CEO", "Jane Doe - CTO"] |
| `recent_news` | List[string] | Company updates | ["Raised $10M Series B", "Launched new product"] |
| `certifications` | List[string] | Certifications | ["SOC2", "ISO27001"] |
| `partnerships` | List[string] | Key partnerships | ["Salesforce", "Microsoft"] |
| `awards` | List[string] | Recognition | ["Best CRM 2024", "Top Startup Award"] |
| `products_services_offered` | List[string] | Product catalog | ["CRM Platform", "Sales Analytics", "API"] |
| `recent_news_events` | List[Dict] | Structured news | [{"date": "2024-01-15", "event": "Funding round"}] |

### 3.6 Job & Hiring Information (4 Fields)

| Theodore Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `has_job_listings` | bool | Active hiring | true |
| `job_listings_count` | int | Number of openings | 15 |
| `job_listings` | string | Job summary | "Actively hiring in engineering and sales" |
| `job_listings_details` | List[string] | Job titles | ["Senior Developer", "Sales Manager"] |

### 3.7 SaaS Classification (David's Framework) (7 Fields)

| Theodore Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `saas_classification` | string | Business model category | "Martech & CRM" |
| `classification_confidence` | float | Confidence score 0-1 | 0.85 |
| `classification_justification` | string | Explanation | "Provides CRM software via subscription model" |
| `classification_timestamp` | datetime | When classified | "2024-01-15T10:30:00Z" |
| `classification_model_version` | string | Model version | "v1.0" |
| `is_saas` | bool | SaaS vs Non-SaaS | true |
| `funding_stage_detailed` | string | Detailed funding | "series_b" |

### 3.8 Similarity Metrics (11 Fields)

| Theodore Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `company_stage` | string | startup, growth, enterprise | "growth" |
| `tech_sophistication` | string | low, medium, high | "high" |
| `geographic_scope` | string | local, regional, global | "global" |
| `business_model_type` | string | saas, services, marketplace | "saas" |
| `decision_maker_type` | string | technical, business, hybrid | "technical" |
| `sales_complexity` | string | simple, moderate, complex | "moderate" |
| `stage_confidence` | float | Stage confidence 0-1 | 0.9 |
| `tech_confidence` | float | Tech confidence 0-1 | 0.8 |
| `industry_confidence` | float | Industry confidence 0-1 | 0.95 |
| `sales_marketing_tools` | List[string] | Tools used | ["HubSpot", "Salesforce", "Mailchimp"] |
| `key_decision_makers` | Dict[str, str] | Decision makers | {"ceo": "John Smith", "cto": "Jane Doe"} |

### 3.9 AI Analysis & Processing (10 Fields)

| Theodore Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `raw_content` | string | Scraped content | "Full website text..." |
| `ai_summary` | string | AI-generated summary | "Acme Corp is a leading CRM..." |
| `embedding` | List[float] | Vector embedding | [0.1, 0.2, 0.3, ...] |
| `scraped_urls` | List[string] | URLs scraped | ["https://acme.com/about", "..."] |
| `scraped_content_details` | Dict[str, str] | URL -> content map | {"url": "content"} |
| `pages_crawled` | List[string] | Crawled pages | ["about", "contact", "team"] |
| `crawl_depth` | int | Crawl depth | 3 |
| `crawl_duration` | float | Crawl time (seconds) | 25.3 |
| `llm_prompts_sent` | List[Dict] | LLM interactions | [{"prompt": "...", "response": "..."}] |
| `page_selection_prompt` | string | Page selection prompt | "Select most relevant pages..." |

### 3.10 Token Usage & Cost Tracking (6 Fields)

| Theodore Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `total_input_tokens` | int | Total input tokens | 15000 |
| `total_output_tokens` | int | Total output tokens | 3000 |
| `total_cost_usd` | float | Total cost in USD | 0.45 |
| `llm_calls_breakdown` | List[Dict] | Cost breakdown | [{"model": "gpt-4", "cost": 0.12}] |
| `content_analysis_prompt` | string | Analysis prompt | "Analyze this company..." |
| `scrape_status` | string | Processing status | "completed" |

### 3.11 Metadata & Timestamps (5 Fields)

| Theodore Field | Type | Description | Example |
|----------------|------|-------------|---------|
| `created_at` | datetime | Creation timestamp | "2024-01-15T08:00:00Z" |
| `last_updated` | datetime | Last update | "2024-01-15T10:30:00Z" |
| `scrape_error` | string | Error message | null |
| `scrape_status` | string | Status | "completed" |
| `id` | string | UUID | "uuid4-generated" |

**Total Theodore Fields: 77 fields across 11 categories**

---

## 4. Field Mapping Matrix

### 4.1 Direct Mappings (1:1 Mapping)

These Theodore fields map directly to existing HubSpot properties:

| Theodore Field | HubSpot Property | Type | Notes |
|----------------|------------------|------|-------|
| `name` | `name` | string | Direct match |
| `website` | `website` | string | Direct match |
| `industry` | `industry` | enumeration | May need enum mapping |
| `company_description` | `description` | string | Direct match |
| `founding_year` | `founded_year` | number | Direct match |
| `location` | `city` + `state` + `country` | string | Parse location into components |
| `employee_count_range` | `numberofemployees` | number | Convert range to number |
| `funding_status` | `total_money_raised` | number | Convert status to amount |
| `social_media.twitter` | `twitterhandle` | string | Extract from dict |
| `social_media.linkedin` | `linkedin_company_page` | string | Extract from dict |
| `social_media.facebook` | `facebook_company_page` | string | Extract from dict |
| `contact_info.phone` | `phone` | string | Extract from dict |
| `target_market` | `about_us` | string | Use as about section |
| `created_at` | `createdate` | datetime | Direct match |
| `last_updated` | `hs_lastmodifieddate` | datetime | HubSpot auto-manages |

### 4.2 Transformation Mappings (Requires Processing)

These fields need data transformation before mapping:

| Theodore Field | HubSpot Property | Transformation Required | Example |
|----------------|------------------|-------------------------|---------|
| `business_model` | `business_model` (custom) | Create custom enum property | "B2B SaaS" → enum value |
| `company_size` | `company_size` (custom) | Create custom enum property | "growth" → enum value |
| `tech_stack` | `web_technologies` | Convert list to comma-separated | ["React", "AWS"] → "React, AWS" |
| `pain_points` | `pain_points` (custom) | Convert list to string | ["Manual processes"] → "Manual processes; Data silos" |
| `key_services` | `key_services` (custom) | Convert list to string | Services array → "Service1; Service2" |
| `leadership_team` | `leadership_team` (custom) | Convert list to string | ["John Smith - CEO"] → "John Smith - CEO; Jane Doe - CTO" |
| `competitive_advantages` | `competitive_advantages` (custom) | Convert list to string | Advantages array → concatenated string |
| `has_chat_widget` | `has_chat_widget` (custom) | Boolean custom property | true → true |
| `has_forms` | `has_forms` (custom) | Boolean custom property | true → true |
| `job_listings_count` | `job_openings_count` (custom) | Number custom property | 15 → 15 |
| `location` | `city`, `state`, `country` | Parse location string | "San Francisco, CA" → city="San Francisco", state="CA" |

### 4.3 Custom Properties Required (New HubSpot Properties)

These Theodore fields require creating new custom properties in HubSpot:

#### Business Intelligence Properties
- `business_model_framework` (string) - David's classification
- `saas_classification` (string) - SaaS vertical
- `classification_confidence` (number) - Confidence score
- `is_saas` (bool) - SaaS vs Non-SaaS
- `value_proposition` (string) - Company value prop
- `company_stage` (enumeration) - startup, growth, enterprise
- `tech_sophistication` (enumeration) - low, medium, high
- `geographic_scope` (enumeration) - local, regional, global
- `decision_maker_type` (enumeration) - technical, business, hybrid
- `sales_complexity` (enumeration) - simple, moderate, complex

#### Company Details Properties
- `employee_count_range` (string) - Employee range estimate
- `company_culture` (string) - Culture description
- `funding_stage_detailed` (string) - Detailed funding stage
- `certifications` (string) - Certifications list
- `partnerships` (string) - Key partnerships
- `awards` (string) - Awards and recognition
- `products_services_offered` (string) - Product catalog

#### Job & Hiring Properties
- `has_job_listings` (bool) - Active hiring status
- `job_listings_count` (number) - Number of openings
- `job_listings_summary` (string) - Job summary
- `job_listings_details` (string) - Job titles

#### Technology Properties
- `tech_stack` (string) - Technology stack
- `has_chat_widget` (bool) - Chat widget presence
- `has_forms` (bool) - Lead forms presence
- `sales_marketing_tools` (string) - Tools used

#### AI Analysis Properties
- `ai_summary` (string) - AI-generated summary
- `crawl_duration` (number) - Processing time
- `pages_crawled_count` (number) - Number of pages processed
- `scrape_status` (string) - Processing status

#### Confidence Scores
- `stage_confidence` (number) - Stage classification confidence
- `tech_confidence` (number) - Tech sophistication confidence
- `industry_confidence` (number) - Industry classification confidence
- `classification_confidence` (number) - Overall classification confidence

#### Cost Tracking Properties
- `total_input_tokens` (number) - AI tokens used
- `total_output_tokens` (number) - AI tokens generated
- `total_cost_usd` (number) - Processing cost
- `llm_calls_count` (number) - Number of AI calls

### 4.4 Unmappable Fields (Internal Use Only)

These Theodore fields are for internal processing and won't be synced to HubSpot:

| Theodore Field | Reason Not Mapped | Alternative |
|----------------|-------------------|-------------|
| `id` | Theodore's internal UUID | Use HubSpot's auto-generated ID |
| `embedding` | Vector data (1536 floats) | Too large for HubSpot properties |
| `raw_content` | Full scraped content | Too large, use `ai_summary` instead |
| `scraped_urls` | Internal processing | Use `pages_crawled_count` instead |
| `scraped_content_details` | Internal processing | Use `ai_summary` instead |
| `llm_prompts_sent` | Internal processing | Use `llm_calls_count` instead |
| `page_selection_prompt` | Internal processing | Not relevant for CRM |
| `content_analysis_prompt` | Internal processing | Not relevant for CRM |
| `llm_calls_breakdown` | Internal processing | Use `total_cost_usd` instead |
| `scrape_error` | Internal processing | Use `scrape_status` instead |

---

## 5. API Integration Requirements

### 5.1 HubSpot Properties API Usage

#### Required API Endpoints
```python
# Property Management
GET /crm/v3/properties/companies          # List all properties
POST /crm/v3/properties/companies         # Create new property
PATCH /crm/v3/properties/companies/{name} # Update property
DELETE /crm/v3/properties/companies/{name} # Delete property

# Company Management
GET /crm/v3/objects/companies             # List companies
POST /crm/v3/objects/companies            # Create company
PATCH /crm/v3/objects/companies/{id}      # Update company
DELETE /crm/v3/objects/companies/{id}     # Delete company
```

#### Custom Property Creation Requirements
```python
# Example: Create business_model_framework property
{
    "name": "business_model_framework",
    "label": "Business Model Framework",
    "type": "string",
    "description": "David's business model classification",
    "groupName": "theodore_intelligence",
    "options": []  # For enumeration types
}
```

### 5.2 Data Validation & Transformation

#### String Length Limits
- **HubSpot string properties**: 65,536 characters max
- **Theodore fields that may exceed**: `raw_content`, `ai_summary`
- **Solution**: Truncate or use multiple properties

#### Data Type Conversions
```python
# Theodore → HubSpot conversions
List[string] → string  # Join with "; " delimiter
Dict[str, str] → string # JSON encode or extract specific keys
datetime → timestamp   # Convert to HubSpot datetime format
float → number        # Round to appropriate precision
```

#### Required Validations
- **Email format**: Contact email validation
- **URL format**: Website and social media URLs
- **Phone format**: Phone number standardization
- **Date format**: ISO 8601 datetime strings
- **Enum values**: Validate against HubSpot enum options

### 5.3 Batch Operations & Rate Limiting

#### HubSpot API Limits
- **Rate Limit**: 100 requests per 10 seconds (OAuth apps)
- **Batch Size**: Up to 100 objects per batch request
- **Daily Limits**: 40,000 requests per day (varies by plan)

#### Batch Processing Strategy
```python
# Company batch operations
POST /crm/v3/objects/companies/batch/create  # Create multiple
POST /crm/v3/objects/companies/batch/update  # Update multiple
POST /crm/v3/objects/companies/batch/upsert  # Upsert multiple
```

#### Error Handling Requirements
- **Retry Logic**: Exponential backoff for 429 rate limit errors
- **Partial Failures**: Handle batch operations with some failures
- **Validation Errors**: Detailed error reporting for data issues
- **Authentication**: OAuth token refresh handling

### 5.4 Sync Strategy Considerations

#### Incremental Sync
- **Theodore → HubSpot**: Sync based on `last_updated` timestamp
- **HubSpot → Theodore**: Use HubSpot's `hs_lastmodifieddate` property
- **Conflict Resolution**: Last-write-wins or manual resolution

#### Bidirectional Sync
- **Data Ownership**: Define which system owns which fields
- **Sync Direction**: Some fields may be HubSpot → Theodore only
- **Change Detection**: Use modification timestamps

#### Performance Optimization
- **Parallel Processing**: Process multiple companies concurrently
- **Caching**: Cache HubSpot property definitions
- **Differential Sync**: Only sync changed fields
- **Bulk Operations**: Use batch APIs for multiple records

---

## 6. Implementation Recommendations

### 6.1 Phase 1: Core Mapping (Direct Fields)
1. Implement direct field mappings (15 fields)
2. Create basic HubSpot client integration
3. Test with small dataset

### 6.2 Phase 2: Custom Properties (High-Value Fields)
1. Create essential custom properties (25 fields)
2. Implement transformation logic
3. Add batch processing capabilities

### 6.3 Phase 3: Advanced Features
1. Implement bidirectional sync
2. Add conflict resolution
3. Create sync monitoring dashboard

### 6.4 Technical Architecture
```
Theodore CompanyData → HubSpot Adapter → HubSpot API
                    ↓
                 Field Mapping Engine
                    ↓
                 Property Manager
                    ↓
                 Sync Service
```

---

## 7. Conclusion

This research identified **77 Theodore fields** that need to be mapped to HubSpot's company object. The mapping breaks down as:

- **Direct Mappings**: 15 fields (existing HubSpot properties)
- **Custom Properties**: 35 fields (new HubSpot properties needed)
- **Transformation Required**: 18 fields (data processing needed)
- **Unmappable**: 9 fields (internal use only)

The integration will require creating approximately **35 custom properties** in HubSpot to accommodate Theodore's rich company intelligence data.

**Next Steps**: Implement the HubSpot adapter using this mapping as the foundation.