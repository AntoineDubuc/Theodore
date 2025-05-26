# Theodore Setup & Configuration Guide

## 🚀 Quick Start Installation

### Prerequisites

- **Python 3.9+** (Python 3.11+ recommended)
- **Git** for version control
- **OpenAI API Key** (required for AI extraction)
- **AWS Account** with Bedrock access (optional but recommended)
- **Pinecone Account** (for vector storage)

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd Theodore

# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your API keys
nano .env  # or use your preferred editor
```

**Required `.env` Configuration:**
```bash
# AI Service Keys (Required)
OPENAI_API_KEY=sk-your-openai-api-key-here

# AWS Configuration (Optional but recommended)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-east-1

# Pinecone Configuration (Required for vector storage)
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=theodore-companies
PINECONE_HOST=your-pinecone-host-url

# Optional: Advanced Configuration
PINECONE_NAMESPACE=production
MAX_CONCURRENT_REQUESTS=5
DEFAULT_BATCH_SIZE=10
```

### 3. Service Setup

#### 3.1 OpenAI Setup
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add it to your `.env` file
4. **Recommended**: Set up usage limits and monitoring

#### 3.2 AWS Bedrock Setup (Optional)
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Request model access (if needed)
# Go to AWS Console > Bedrock > Model Access
# Request access to: amazon.nova-premier-v1:0, amazon.titan-embed-text-v2:0
```

#### 3.3 Pinecone Setup
1. Create account at [Pinecone](https://www.pinecone.io)
2. Create a new index with these settings:
   ```
   Name: theodore-companies
   Dimension: 1536
   Metric: cosine
   Pod Type: p1.x1 (recommended for cost-effectiveness)
   ```
3. Get your API key and host URL from the Pinecone console

### 4. Verification

Test your setup with the verification script:

```bash
# Run system verification
python scripts/verify_setup.py

# Expected output:
# ✅ Python version: 3.11.x
# ✅ Dependencies installed
# ✅ OpenAI API connection successful
# ✅ AWS Bedrock access verified (if configured)
# ✅ Pinecone connection successful
# ✅ Environment configuration valid
```

## 🔧 Development Configuration

### Development Environment

For development work, create a `dev.env` file:

```bash
# Development-specific configuration
OPENAI_API_KEY=sk-your-dev-openai-key
PINECONE_INDEX_NAME=theodore-dev
MAX_COMPANIES=5
ENABLE_DEBUG_LOGGING=true
CRAWL_DELAY=2.0
ENABLE_CACHING=false
```

### Testing Setup

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_single_company.py -v

# Run with coverage
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

### IDE Configuration

**VS Code Setup** (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true
    }
}
```

## 📊 Production Configuration

### Production Environment Variables

```bash
# Production .env configuration
OPENAI_API_KEY=sk-prod-openai-key
AWS_ACCESS_KEY_ID=prod-aws-access-key
AWS_SECRET_ACCESS_KEY=prod-aws-secret
PINECONE_API_KEY=prod-pinecone-key
PINECONE_INDEX_NAME=theodore-production
PINECONE_NAMESPACE=prod

# Performance optimization
MAX_COMPANIES=100
MAX_CONCURRENT_REQUESTS=10
BATCH_SIZE=50
CRAWL_DELAY=1.0
ENABLE_CACHING=true

# Monitoring
ENABLE_METRICS=true
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn  # Optional error tracking
```

### Resource Limits

```bash
# Memory and processing limits
MAX_CONTENT_LENGTH=50000
MAX_PAGES_PER_COMPANY=15
EXTRACTION_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=2.0

# Cost controls
DAILY_API_BUDGET=50.00
MAX_TOKENS_PER_EXTRACTION=4000
ENABLE_COST_TRACKING=true
```

### Scaling Configuration

```bash
# For high-volume processing
ENABLE_BATCH_PROCESSING=true
BATCH_SIZE=100
WORKER_PROCESSES=4
ASYNC_CONCURRENCY=20

# Database connections
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

## 🛠️ Advanced Configuration

### Custom Model Configuration

```python
# config/ai_models.py
AI_MODEL_CONFIG = {
    "extraction": {
        "primary": "openai/gpt-4o-mini",
        "fallback": "openai/gpt-3.5-turbo",
        "temperature": 0.1,
        "max_tokens": 2000
    },
    "analysis": {
        "primary": "anthropic.claude-3-sonnet-20240229-v1:0",
        "fallback": "anthropic.claude-3-haiku-20240307-v1:0",
        "temperature": 0.3,
        "max_tokens": 4000
    },
    "embeddings": {
        "primary": "amazon.titan-embed-text-v2:0",
        "dimension": 1536,
        "normalize": True
    }
}
```

### Custom Processing Configuration

```python
# config/processing.py
PROCESSING_CONFIG = {
    "scraping": {
        "target_pages": [
            "", "/about", "/about-us", "/company",
            "/services", "/products", "/solutions",
            "/team", "/leadership", "/careers", "/contact"
        ],
        "timeout": 20,
        "retry_attempts": 3,
        "delay_between_pages": 1.0,
        "delay_between_companies": 3.0
    },
    "extraction": {
        "enable_schema_validation": True,
        "quality_threshold": 0.7,
        "enable_fallback_extraction": True
    },
    "storage": {
        "enable_vector_storage": True,
        "enable_local_cache": True,
        "metadata_fields": [
            "company_name", "industry", "business_model",
            "target_market", "company_size"
        ]
    }
}
```

## 🔍 Configuration Validation

### Validation Script

Create `scripts/verify_setup.py`:

```python
#!/usr/bin/env python3
"""
Theodore Setup Verification Script
Validates all configuration and service connections
"""

import os
import sys
import asyncio
from typing import Dict, Any
import openai
import pinecone
import boto3
from src.models import CompanyIntelligenceConfig

class SetupValidator:
    def __init__(self):
        self.results = {}
    
    def check_python_version(self) -> bool:
        """Verify Python version compatibility"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 9:
            print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            print(f"❌ Python version {version.major}.{version.minor} not supported. Requires 3.9+")
            return False
    
    def check_environment_variables(self) -> bool:
        """Verify required environment variables"""
        required_vars = ['OPENAI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_INDEX_NAME']
        optional_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        
        missing_required = []
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        if missing_required:
            print(f"❌ Missing required environment variables: {missing_required}")
            return False
        
        print("✅ Required environment variables present")
        
        missing_optional = [var for var in optional_vars if not os.getenv(var)]
        if missing_optional:
            print(f"⚠️  Optional environment variables missing: {missing_optional}")
        
        return True
    
    async def check_openai_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            openai.api_key = os.getenv('OPENAI_API_KEY')
            response = openai.models.list()
            print("✅ OpenAI API connection successful")
            return True
        except Exception as e:
            print(f"❌ OpenAI API connection failed: {e}")
            return False
    
    def check_pinecone_connection(self) -> bool:
        """Test Pinecone connection"""
        try:
            pinecone.init(
                api_key=os.getenv('PINECONE_API_KEY'),
                environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1')
            )
            
            index_name = os.getenv('PINECONE_INDEX_NAME')
            if index_name in pinecone.list_indexes():
                print("✅ Pinecone connection successful")
                return True
            else:
                print(f"❌ Pinecone index '{index_name}' not found")
                return False
        except Exception as e:
            print(f"❌ Pinecone connection failed: {e}")
            return False
    
    def check_aws_bedrock(self) -> bool:
        """Test AWS Bedrock access (optional)"""
        try:
            if not os.getenv('AWS_ACCESS_KEY_ID'):
                print("ℹ️  AWS credentials not configured (optional)")
                return True
            
            client = boto3.client('bedrock', region_name='us-east-1')
            response = client.list_foundation_models()
            print("✅ AWS Bedrock access verified")
            return True
        except Exception as e:
            print(f"⚠️  AWS Bedrock access failed: {e} (optional)")
            return True  # Non-critical for basic functionality
    
    def check_dependencies(self) -> bool:
        """Verify all required packages are installed"""
        try:
            import crawl4ai
            import pydantic
            import pinecone
            import openai
            import boto3
            print("✅ All dependencies installed")
            return True
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            return False
    
    async def run_validation(self) -> Dict[str, bool]:
        """Run all validation checks"""
        print("🔍 Validating Theodore Setup...\n")
        
        checks = [
            ("Python Version", self.check_python_version()),
            ("Dependencies", self.check_dependencies()),
            ("Environment Variables", self.check_environment_variables()),
            ("OpenAI Connection", await self.check_openai_connection()),
            ("Pinecone Connection", self.check_pinecone_connection()),
            ("AWS Bedrock", self.check_aws_bedrock())
        ]
        
        results = {}
        for name, result in checks:
            results[name] = result
        
        print(f"\n📊 Validation Summary:")
        passed = sum(results.values())
        total = len(results)
        print(f"✅ {passed}/{total} checks passed")
        
        if passed == total:
            print("🎉 Theodore is ready for use!")
        else:
            print("❌ Please fix the failing checks before proceeding")
        
        return results

async def main():
    validator = SetupValidator()
    await validator.run_validation()

if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration Debugging

```python
# scripts/debug_config.py
def debug_configuration():
    """Debug current configuration state"""
    
    print("🔧 Theodore Configuration Debug\n")
    
    # Environment variables
    env_vars = [
        'OPENAI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_INDEX_NAME',
        'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION'
    ]
    
    print("Environment Variables:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'SECRET' in var:
                masked_value = f"{value[:8]}...{value[-4:]}"
                print(f"  {var}: {masked_value}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: ❌ Not set")
    
    # Model configuration
    config = CompanyIntelligenceConfig()
    print(f"\nProcessing Configuration:")
    print(f"  Max Companies: {config.max_companies}")
    print(f"  Max Content Length: {config.max_content_length}")
    print(f"  Enable Clustering: {config.enable_clustering}")
    
    # File system
    print(f"\nFile System:")
    print(f"  Current Directory: {os.getcwd()}")
    print(f"  Data Directory: {'✅ Exists' if os.path.exists('data') else '❌ Missing'}")
    print(f"  Logs Directory: {'✅ Exists' if os.path.exists('logs') else '❌ Missing'}")
```

## 🐳 Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMIUM_PATH=/usr/bin/chromium

# Expose port (if running web interface)
EXPOSE 8000

# Default command
CMD ["python", "src/main_pipeline.py"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  theodore:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    mem_limit: 2g
    cpus: 1.0

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: theodore
      POSTGRES_USER: theodore
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

## 🔄 Maintenance & Updates

### Regular Maintenance Tasks

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Clear cached data
python scripts/clear_cache.py

# Health check
python scripts/health_check.py

# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)
```

### Monitoring Setup

```bash
# Install monitoring dependencies
pip install prometheus-client sentry-sdk

# Configure monitoring
export SENTRY_DSN=your-sentry-dsn
export PROMETHEUS_PORT=8001
```

---

## 🆘 Troubleshooting

### Common Issues

1. **ModuleNotFoundError**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **API Rate Limits**
   ```bash
   # Reduce concurrency in .env
   MAX_CONCURRENT_REQUESTS=3
   CRAWL_DELAY=2.0
   ```

3. **Memory Issues**
   ```bash
   # Reduce batch size
   BATCH_SIZE=10
   MAX_CONTENT_LENGTH=20000
   ```

4. **Pinecone Connection Issues**
   ```bash
   # Verify index exists
   python -c "import pinecone; pinecone.init(); print(pinecone.list_indexes())"
   ```

For additional support, check the [troubleshooting documentation](./TROUBLESHOOTING.md) or review the logs in the `logs/` directory.

---

*This setup guide covers everything needed to get Theodore running in development and production environments.*