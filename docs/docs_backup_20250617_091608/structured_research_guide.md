# Theodore Structured Research System

## 🎯 Overview

Theodore's Structured Research System provides predefined research prompts with cost transparency, session management, and export capabilities. This system implements the requirements from the AI-Powered Company List Enrichment Tool PRD.

## 📋 Research Prompt Library

### Available Research Categories

#### 1. **Job Listings Analysis** (`job_listings`)
- **Purpose**: Identify current open positions and hiring trends
- **Output**: JSON format with hiring indicators
- **Estimated Tokens**: 800
- **Key Insights**: Active positions, growth patterns, remote work policies

#### 2. **Key Decision Makers** (`decision_makers`)
- **Purpose**: Identify leadership team and decision makers
- **Output**: JSON format with structured leadership data
- **Estimated Tokens**: 600
- **Key Insights**: CEO/Founder, CMO, CTO, VP Sales, LinkedIn profiles

#### 3. **Products & Services Analysis** (`products_services`)
- **Purpose**: Comprehensive analysis of company offerings
- **Output**: JSON format with detailed product information
- **Estimated Tokens**: 900
- **Key Insights**: Core offerings, pricing models, value propositions

#### 4. **Funding & Investment Analysis** (`funding_stage`)
- **Purpose**: Research funding history and investment stage
- **Output**: JSON format with funding details
- **Estimated Tokens**: 700
- **Key Insights**: Funding rounds, investors, valuation, financial health

#### 5. **Technology Stack Analysis** (`tech_stack`)
- **Purpose**: Identify technologies and tools used
- **Output**: JSON format categorizing technologies by type
- **Estimated Tokens**: 750
- **Key Insights**: Programming languages, cloud platforms, security tools

#### 6. **Recent News & Events** (`recent_news`)
- **Purpose**: Latest company news, announcements, and milestones
- **Output**: JSON format with chronological news items
- **Estimated Tokens**: 650
- **Key Insights**: Press releases, partnerships, media coverage

#### 7. **Competitive Landscape** (`competitive_landscape`)
- **Purpose**: Identify competitors and market positioning
- **Output**: JSON format with competitive intelligence
- **Estimated Tokens**: 800
- **Key Insights**: Direct competitors, market category, differentiation

#### 8. **Customer Base Analysis** (`customer_analysis`)
- **Purpose**: Understand target customers and use cases
- **Output**: JSON format with customer insights
- **Estimated Tokens**: 700
- **Key Insights**: Customer segments, company sizes, use cases

## 💰 Cost Structure

### Nova Pro Pricing Model
- **Token Rate**: $0.011 per 1,000 tokens
- **6x Cost Reduction**: Down from $0.66 to $0.11 per average research
- **Transparent Estimation**: Real-time cost calculation before execution

### Cost Examples
```bash
# Single prompt research
Job Listings Analysis: ~800 tokens = $0.0088

# Multi-prompt research (3 prompts)
Job Listings + Decision Makers + Funding: ~2,100 tokens = $0.0231

# Comprehensive research (all 8 prompts)
All categories: ~5,900 tokens = $0.0649
```

## 🔄 Research Session Management

### Session Lifecycle
1. **Session Creation**: Initialize research with selected prompts
2. **Cost Estimation**: Calculate total tokens and cost
3. **Execution**: Run prompts with progress tracking
4. **Results Collection**: Gather and parse responses
5. **Session Completion**: Calculate success rates and metrics
6. **Export Options**: JSON or CSV format export

### Session Metrics
- **Success Rate**: Percentage of prompts completed successfully
- **Total Cost**: Actual cost in dollars
- **Total Tokens**: Token usage across all prompts
- **Execution Time**: Time per prompt and total session time
- **Error Tracking**: Detailed error messages for failed prompts

## 🚀 API Usage Guide

### 1. Get Available Prompts
```bash
GET /api/research/prompts/available

Response:
{
  "success": true,
  "prompts": {
    "total_prompts": 8,
    "categories": {
      "hiring": {
        "count": 1,
        "prompts": [{"id": "job_listings", "name": "Job Listings Analysis"}]
      }
    }
  }
}
```

### 2. Estimate Research Cost
```bash
POST /api/research/prompts/estimate
{
  "selected_prompts": ["job_listings", "decision_makers", "funding_stage"]
}

Response:
{
  "success": true,
  "cost_estimate": {
    "total_tokens": 2100,
    "total_cost": 0.0231,
    "cost_per_company": 0.0231,
    "prompt_details": [...]
  }
}
```

### 3. Start Structured Research
```bash
POST /api/research/structured/start
{
  "company_name": "OpenAI",
  "website": "https://openai.com",
  "selected_prompts": ["job_listings", "decision_makers"],
  "include_base_research": true
}

Response:
{
  "success": true,
  "session_id": "structured_OpenAI_1703875200",
  "cost_estimate": {...}
}
```

### 4. Monitor Session Progress
```bash
GET /api/research/structured/session/structured_OpenAI_1703875200

Response:
{
  "success": true,
  "session": {
    "session_id": "structured_OpenAI_1703875200",
    "company_name": "OpenAI",
    "start_time": "2025-12-08T10:00:00Z",
    "end_time": "2025-12-08T10:05:00Z",
    "success_rate": 1.0,
    "total_cost": 0.0154,
    "results": [...]
  }
}
```

### 5. Export Results
```bash
# JSON Export
GET /api/research/structured/export/structured_OpenAI_1703875200?format=json

# CSV Export
GET /api/research/structured/export/structured_OpenAI_1703875200?format=csv
```

## 📊 Result Structure

### Session Results Format
```json
{
  "session_metadata": {
    "session_id": "structured_OpenAI_1703875200",
    "company_name": "OpenAI",
    "total_cost": 0.0154,
    "success_rate": 1.0
  },
  "research_results": [
    {
      "prompt_id": "job_listings",
      "prompt_name": "Job Listings Analysis",
      "success": true,
      "result_data": {
        "current_openings": 45,
        "most_common_roles": ["AI Researcher", "Software Engineer"],
        "remote_policy": "Hybrid"
      },
      "cost": 0.0088,
      "execution_time": 12.5
    }
  ]
}
```

### CSV Export Structure
```csv
session_id,company_name,prompt_id,prompt_name,success,cost,result_current_openings,result_remote_policy
structured_OpenAI_1703875200,OpenAI,job_listings,Job Listings Analysis,true,0.0088,45,Hybrid
```

## 🔧 Integration Examples

### Python SDK Usage
```python
from src.research_manager import ResearchManager
from src.research_prompts import research_prompt_library

# Initialize research manager
research_manager = ResearchManager(
    intelligent_scraper=scraper,
    pinecone_client=pinecone_client,
    bedrock_client=bedrock_client
)

# Get cost estimate
selected_prompts = ["job_listings", "decision_makers", "tech_stack"]
cost_estimate = research_manager.estimate_research_cost(selected_prompts)
print(f"Estimated cost: ${cost_estimate['total_cost']:.4f}")

# Start research session
session_id = research_manager.research_company_with_prompts(
    company_name="Stripe",
    website="https://stripe.com",
    selected_prompts=selected_prompts,
    include_base_research=True
)

# Monitor progress
session = research_manager.get_research_session(session_id)
print(f"Success rate: {session.success_rate:.1%}")

# Export results
exported_data = research_manager.export_session_results(session_id, "json")
```

### Web Interface Integration
The structured research system integrates seamlessly with Theodore's existing web interface, providing:

- **Prompt Selection UI**: Interactive checkboxes for research categories
- **Cost Calculator**: Real-time cost estimation as prompts are selected
- **Progress Tracking**: Live updates during research execution
- **Results Viewer**: Structured display of research findings
- **Export Options**: One-click download in JSON or CSV format

## 🛡️ Error Handling

### Common Error Scenarios
1. **Prompt Not Found**: Invalid prompt ID provided
2. **Bedrock API Errors**: Rate limiting or service issues
3. **JSON Parse Failures**: Malformed LLM responses
4. **Session Not Found**: Invalid session ID for retrieval
5. **Export Format Errors**: Unsupported export format

### Error Response Format
```json
{
  "success": false,
  "error": "Prompt 'invalid_prompt' not found",
  "timestamp": "2025-12-08T10:00:00Z"
}
```

## 📈 Performance Optimization

### Concurrent Processing
- **Thread Pool**: Limited to 3 concurrent research operations
- **Rate Limiting**: Respectful API usage with controlled requests
- **Error Recovery**: Graceful handling of individual prompt failures
- **Progress Tracking**: Real-time status updates for long-running sessions

### Cost Optimization
- **Nova Pro Model**: 6x cost reduction over previous Claude Sonnet 4
- **Token Estimation**: Accurate pre-execution cost calculation
- **Selective Prompts**: Choose only relevant research categories
- **Batch Processing**: Efficient handling of multiple prompts per session

## 🔍 Best Practices

### Prompt Selection Strategy
1. **Start Small**: Begin with 2-3 key prompts for initial research
2. **Industry Specific**: Choose prompts relevant to target industry
3. **Cost Conscious**: Use cost estimation to stay within budget
4. **Iterative Approach**: Add more prompts based on initial findings

### Session Management
1. **Monitor Progress**: Check session status regularly
2. **Error Review**: Examine failed prompts for actionable insights
3. **Export Early**: Download results promptly after completion
4. **Clean Up**: Use cleanup API to remove old sessions

### Data Analysis
1. **JSON for Processing**: Use JSON export for automated analysis
2. **CSV for Reporting**: Use CSV export for business reporting
3. **Success Rate Monitoring**: Track research quality over time
4. **Cost Analysis**: Monitor spending patterns and optimize

---

*This guide covers Theodore's Structured Research System implementation based on the AI-Powered Company List Enrichment Tool PRD requirements, delivering cost-effective, comprehensive company intelligence with full transparency and export capabilities.*