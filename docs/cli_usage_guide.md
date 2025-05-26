# Theodore CLI Usage Guide

## Overview
Theodore now includes a comprehensive CLI for company intelligence and similarity discovery operations.

## Installation & Setup

### Prerequisites
```bash
# Ensure environment variables are set
export PINECONE_API_KEY="your-pinecone-key"
export PINECONE_ENVIRONMENT="your-environment" 
export PINECONE_INDEX_NAME="theodore-companies"
export AWS_ACCESS_KEY_ID="your-aws-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret"
export OPENAI_API_KEY="your-openai-key"
```

### Quick Start
```bash
# Make CLI executable
chmod +x theodore_cli.py

# View all available commands
./theodore_cli.py --help
```

## Available Commands

### 1. **Company Processing Commands**

#### Process Survey CSV
```bash
./theodore_cli.py process-survey --input-csv companies.csv --output-csv results.csv
```
Process a CSV of company survey data and generate intelligence reports.

#### Process Single Company
```bash
./theodore_cli.py process-single --company "Acme Corp:https://acme.com"
```
Process a single company and generate intelligence.

### 2. **🆕 Similarity Discovery Commands**

#### Discover Similar Companies
```bash
# Basic discovery
./theodore_cli.py discover-similar "Salesforce"

# With custom limit and output file
./theodore_cli.py discover-similar "Salesforce" --limit 10 --output similarities.json
```

**Example Output:**
```
🔍 Discovering companies similar to: Salesforce
==================================================
✅ Found 5 similar companies:

1. HubSpot
   Similarity Score: 0.87
   Confidence: 0.93
   Relationship: competitor
   Reasoning: Both provide CRM solutions; Similar B2B SaaS model

2. Microsoft Dynamics
   Similarity Score: 0.82
   Confidence: 0.89
   Relationship: competitor
   Reasoning: Enterprise CRM platform; Similar target market

...
```

#### Batch Discover Similarities
```bash
./theodore_cli.py batch-discover --input-csv companies_list.csv --output-csv all_similarities.csv --limit 5
```

**Input CSV Format:**
```csv
company_name,company_id
Salesforce,salesforce-123
HubSpot,hubspot-456
Slack,slack-789
```

**Output CSV Format:**
```csv
original_company_name,similar_company_name,similarity_score,confidence,relationship_type,discovery_method,reasoning
Salesforce,HubSpot,0.87,0.93,competitor,llm_pipeline,Both provide CRM solutions
Salesforce,Microsoft Dynamics,0.82,0.89,competitor,llm_pipeline,Enterprise CRM platform
...
```

#### Query Existing Similarities
```bash
# Table format (default)
./theodore_cli.py query-similar "Salesforce" --limit 10

# JSON format
./theodore_cli.py query-similar "Salesforce" --format json --limit 5
```

**Table Output:**
```
🔎 Querying similarities for: Salesforce
========================================
📊 Found 3 existing similarities:

#   Company Name                   Score    Type         Discovered  
----------------------------------------------------------------------
1   HubSpot                        0.87     competitor   2025-01-26  
2   Microsoft Dynamics             0.82     competitor   2025-01-26  
3   Pipedrive                      0.75     adjacent     2025-01-26  
```

## Real-World Usage Examples

### Example 1: David's Survey Processing
```bash
# 1. Process survey companies
./theodore_cli.py process-survey --input-csv survey_responses.csv --output-csv processed_companies.csv

# 2. Discover similarities for all companies
./theodore_cli.py batch-discover --input-csv processed_companies.csv --output-csv company_similarities.csv

# 3. Query specific company
./theodore_cli.py query-similar "CloudGeometry" --format table
```

### Example 2: Competitive Analysis
```bash
# Discover competitors for a specific company
./theodore_cli.py discover-similar "Stripe" --limit 8 --output stripe_competitors.json

# Check what we already know about a company
./theodore_cli.py query-similar "Square" --format json
```

### Example 3: Market Research
```bash
# Process a list of companies in a specific sector
./theodore_cli.py batch-discover --input-csv fintech_companies.csv --output-csv fintech_similarities.csv --limit 3

# Look at individual results
./theodore_cli.py query-similar "PayPal" --limit 15
```

## CLI Command Reference

### Global Options
- `--help` - Show help message
- All commands support verbose logging via environment variables

### Command-Specific Options

#### `discover-similar`
- `company_name` (required) - Name of company to find similarities for
- `--limit` (default: 5) - Maximum similar companies to find
- `--output` (optional) - Save results to JSON file

#### `batch-discover`
- `--input-csv` (required) - CSV with company_name,company_id columns
- `--output-csv` (required) - Output CSV file path
- `--limit` (default: 3) - Similar companies per input company

#### `query-similar`
- `company_name` (required) - Company to query similarities for
- `--limit` (default: 10) - Maximum results to show
- `--format` (table|json, default: table) - Output format

## Error Handling

### Common Issues

1. **Company Not Found**
```
❌ Company 'Unknown Corp' not found in database
💡 Try processing the company first with: process-single --company 'name:website'
```

2. **No Similarities Found**
```
🤷 No similar companies found for ExampleCorp
```

3. **Invalid CSV Format**
```
❌ No valid company data found in input.csv
💡 CSV should have columns: company_name, company_id
```

## Performance & Costs

### Expected Performance
- **Single Discovery**: ~2-3 minutes per company (includes crawling 3-5 candidates)
- **Batch Processing**: ~5-10 companies per hour (with rate limiting)
- **Query Operations**: Near-instant (retrieves from storage)

### Estimated Costs
- **Discovery**: ~$0.25-0.50 per company (LLM calls + crawling)
- **Querying**: ~$0.00 (reads from storage)
- **Batch of 10**: ~$2.50-5.00

### Cost Optimization Tips
```bash
# Use smaller limits to reduce costs
./theodore_cli.py discover-similar "Company" --limit 3

# Query existing data instead of re-discovering
./theodore_cli.py query-similar "Company" --limit 10
```

## Integration with Existing Workflows

### HubSpot Integration Ready
The CSV output format is designed to be easily imported into CRM systems:

```bash
# Generate HubSpot-ready similarity data
./theodore_cli.py batch-discover --input-csv survey_companies.csv --output-csv hubspot_import.csv
```

### Automation Scripts
```bash
#!/bin/bash
# Daily similarity discovery
./theodore_cli.py batch-discover --input-csv daily_companies.csv --output-csv daily_similarities.csv --limit 5

# Email results (example)
mail -s "Daily Similarity Report" team@company.com < daily_similarities.csv
```

## Troubleshooting

### Environment Issues
```bash
# Check if environment variables are set
env | grep -E "(PINECONE|AWS|OPENAI)"

# Test basic functionality
./theodore_cli.py --help
```

### Debugging
```bash
# Enable verbose logging
export THEODORE_LOG_LEVEL=DEBUG
./theodore_cli.py discover-similar "Test Company"
```

## Next Steps

The CLI is now ready for:
1. **Production Use**: Process David's 400 survey companies
2. **Integration**: Connect with HubSpot API workflows  
3. **Automation**: Set up scheduled similarity discovery
4. **Scaling**: Handle larger company datasets

**Ready to discover similar companies at scale! 🚀**