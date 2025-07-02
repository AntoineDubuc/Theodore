# Theodore v2 Technical Specification

## 🛠️ Technology Stack

### Core Technologies

#### **Language & Runtime**
- **Python 3.11+** - Modern Python with type hints and async support
- **Poetry** - Dependency management and packaging
- **pyproject.toml** - Modern Python project configuration

#### **CLI Framework**
- **Click 8.1+** - Command-line interface creation
- **Rich** - Beautiful terminal formatting and progress bars
- **Typer** (alternative) - Type-hint based CLI framework

#### **Async Framework**
- **asyncio** - Native Python async/await
- **aiohttp** - Async HTTP client/server
- **httpx** - Modern async HTTP client with HTTP/2 support

#### **API Framework (for optional web interface)**
- **FastAPI** - Modern, fast web framework with automatic API docs
- **Pydantic v2** - Data validation using Python type annotations
- **Uvicorn** - Lightning-fast ASGI server

#### **Queue & Background Tasks**
- **Celery 5.3+** - Distributed task queue
- **Redis** - Message broker and cache
- **Flower** - Real-time Celery monitoring

#### **Database & Storage**
- **SQLAlchemy 2.0** - SQL toolkit with async support
- **PostgreSQL** - Primary relational database
- **Pinecone** - Vector database for embeddings
- **Alembic** - Database migrations

#### **Testing**
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **hypothesis** - Property-based testing
- **factory-boy** - Test data generation

#### **Documentation**
- **Sphinx** - Documentation generation
- **mkdocs-material** - Beautiful documentation site
- **pydoc-markdown** - Auto-generate API docs from docstrings

#### **Development Tools**
- **Black** - Code formatting
- **Ruff** - Fast Python linter
- **mypy** - Static type checking
- **pre-commit** - Git hooks for code quality

#### **Observability**
- **OpenTelemetry** - Distributed tracing
- **Prometheus** - Metrics collection
- **structlog** - Structured logging
- **Sentry** - Error tracking

#### **Deployment**
- **Docker** - Containerization
- **docker-compose** - Local development
- **Kubernetes** - Production orchestration (optional)
- **GitHub Actions** - CI/CD

## 🔌 API Endpoints

### Core Research Endpoints

```python
# Base URL: http://localhost:8000/api/v2

# Company Research
POST   /research                    # Start company research
GET    /research/{task_id}          # Get research status/results
DELETE /research/{task_id}          # Cancel research task

# Company Discovery  
POST   /discover                    # Find similar companies
GET    /discover/{task_id}          # Get discovery results

# Company Management
GET    /companies                   # List all companies
GET    /companies/{id}              # Get company details
PUT    /companies/{id}              # Update company data
DELETE /companies/{id}              # Delete company

# Batch Operations
POST   /batch/research              # Bulk research multiple companies
GET    /batch/{batch_id}            # Get batch status
GET    /batch/{batch_id}/results    # Get batch results

# Search & Query
POST   /search                      # Search companies with filters
POST   /query                       # Advanced vector similarity search

# Export & Import
GET    /export                      # Export data (CSV, JSON, Excel)
POST   /import                      # Import companies from file

# Plugin Management
GET    /plugins                     # List installed plugins
POST   /plugins/install             # Install a plugin
DELETE /plugins/{name}              # Uninstall plugin
GET    /plugins/{name}/config       # Get plugin configuration
PUT    /plugins/{name}/config       # Update plugin configuration

# System & Health
GET    /health                      # Health check
GET    /metrics                     # Prometheus metrics
GET    /version                     # API version info
GET    /config                      # Current configuration

# WebSocket Endpoints
WS     /ws/progress/{task_id}       # Real-time progress updates
WS     /ws/events                   # System event stream
```

### Detailed Endpoint Specifications

#### **POST /research**
```python
# Request
{
    "company_name": "Apple Inc",
    "website": "https://apple.com",
    "options": {
        "max_pages": 50,
        "deep_analysis": true,
        "force_refresh": false,
        "scrapers": ["crawl4ai", "playwright"],  # Use specific scrapers
        "ai_providers": ["gemini", "bedrock"],   # Use specific AI providers
        "custom_prompts": {
            "extraction": "Focus on sustainability initiatives"
        }
    }
}

# Response
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "queued",
    "created_at": "2024-01-20T10:30:00Z",
    "estimated_time": 45,
    "queue_position": 3
}
```

#### **GET /research/{task_id}**
```python
# Response
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "progress": {
        "current_phase": 4,
        "total_phases": 4,
        "phase_details": {
            "name": "AI Analysis",
            "progress": 100
        }
    },
    "result": {
        "company": {
            "id": "apple-inc-2024",
            "name": "Apple Inc",
            "website": "https://apple.com",
            "industry": "Technology",
            "business_model": "B2C Hardware/Software",
            "company_size": "150,000+",
            "founded": 1976,
            "location": "Cupertino, CA"
        },
        "intelligence": {
            "description": "Apple Inc. designs, manufactures...",
            "value_proposition": "Premium consumer electronics...",
            "competitive_advantages": ["Brand loyalty", "Ecosystem"],
            "market_position": "Market leader"
        },
        "metadata": {
            "pages_scraped": 25,
            "tokens_used": 15420,
            "processing_time": 42.3,
            "confidence_scores": {
                "industry": 0.95,
                "size": 0.88
            }
        }
    }
}
```

#### **POST /plugins/install**
```python
# Request
{
    "source": "github:user/theodore-mcp-websearch",
    "version": "1.0.0",
    "config": {
        "api_key": "your-api-key",
        "max_results": 10
    }
}

# Response
{
    "plugin": {
        "name": "theodore-mcp-websearch",
        "version": "1.0.0",
        "status": "installed",
        "provides": ["WebSearchPort"],
        "author": "user",
        "description": "MCP-based web search plugin"
    }
}
```

## 🔧 Plugin System Architecture

### Plugin Structure

```bash
theodore-mcp-websearch/
├── plugin.yaml                 # Plugin metadata
├── pyproject.toml             # Python package info
├── README.md                  # Documentation
├── src/
│   ├── __init__.py
│   ├── plugin.py              # Main plugin class
│   ├── mcp_adapter.py         # MCP integration
│   └── search_provider.py     # Search implementation
├── tests/
│   └── test_plugin.py
└── examples/
    └── config.yaml
```

### Plugin Metadata (plugin.yaml)

```yaml
# plugin.yaml
name: theodore-mcp-websearch
version: 1.0.0
description: MCP-based web search plugin for Theodore
author: YourName
license: MIT

# Plugin entry point
entry_point: MCPWebSearchPlugin

# What interfaces this plugin provides
provides:
  - interface: WebSearchPort
    implementation: MCPWebSearchProvider

# Dependencies
requires:
  theodore: ">=2.0.0"
  python: ">=3.11"

# External dependencies
dependencies:
  - mcp-sdk>=1.0.0
  - httpx>=0.24.0

# Configuration schema
config_schema:
  type: object
  properties:
    api_key:
      type: string
      description: API key for search service
    endpoint:
      type: string
      default: "https://api.searchprovider.com"
    max_results:
      type: integer
      default: 10
    timeout:
      type: integer
      default: 30
  required:
    - api_key

# Capabilities
capabilities:
  - web_search
  - news_search
  - academic_search
  
# MCP server configuration
mcp:
  server_command: "python -m theodore_mcp_websearch.server"
  transport: stdio
```

### Plugin Implementation

```python
# src/plugin.py
from theodore.plugins.base import Plugin
from theodore.core.interfaces import WebSearchPort
from typing import Dict, Any, List, Type
from .mcp_adapter import MCPWebSearchAdapter

class MCPWebSearchPlugin(Plugin):
    """MCP-based web search plugin"""
    
    @property
    def name(self) -> str:
        return "theodore-mcp-websearch"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def get_dependencies(self) -> List[str]:
        return ["mcp-sdk>=1.0.0", "httpx>=0.24.0"]
    
    def get_provided_interfaces(self) -> Dict[Type, Type]:
        return {
            WebSearchPort: MCPWebSearchProvider
        }
    
    def initialize(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.adapter = MCPWebSearchAdapter(config)
        self.adapter.start_mcp_server()
    
    def shutdown(self) -> None:
        self.adapter.stop_mcp_server()

# src/search_provider.py
from theodore.core.interfaces import WebSearchPort
from typing import List, Dict, Any
import asyncio

class MCPWebSearchProvider(WebSearchPort):
    """Web search implementation using MCP"""
    
    def __init__(self, adapter: MCPWebSearchAdapter):
        self.adapter = adapter
    
    async def search(self, 
                    query: str, 
                    num_results: int = 10,
                    search_type: str = "web") -> List[Dict[str, Any]]:
        """Execute web search via MCP"""
        
        # Call MCP server
        results = await self.adapter.execute_search({
            "query": query,
            "num_results": num_results,
            "type": search_type
        })
        
        # Transform to Theodore format
        return [
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "snippet": r.get("snippet"),
                "relevance_score": r.get("score", 0.0)
            }
            for r in results
        ]
    
    async def get_page_content(self, url: str) -> str:
        """Fetch and extract page content"""
        return await self.adapter.fetch_content(url)

# src/mcp_adapter.py
import subprocess
import json
from typing import Dict, Any, List

class MCPWebSearchAdapter:
    """Adapter for MCP (Model Context Protocol) integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.process = None
        
    def start_mcp_server(self):
        """Start the MCP server process"""
        cmd = [
            "python", "-m", "theodore_mcp_websearch.server",
            "--api-key", self.config["api_key"],
            "--endpoint", self.config.get("endpoint", "https://api.searchprovider.com")
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    async def execute_search(self, params: Dict[str, Any]) -> List[Dict]:
        """Execute search via MCP protocol"""
        
        # Send request to MCP server
        request = {
            "jsonrpc": "2.0",
            "method": "search",
            "params": params,
            "id": 1
        }
        
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        response = json.loads(response_line)
        
        if "error" in response:
            raise Exception(f"MCP error: {response['error']}")
            
        return response["result"]
    
    def stop_mcp_server(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            self.process.wait()
```

### Core Interface for Plugins

```python
# theodore/core/interfaces/websearch.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class WebSearchPort(ABC):
    """Port for web search operations"""
    
    @abstractmethod
    async def search(self, 
                    query: str, 
                    num_results: int = 10,
                    search_type: str = "web") -> List[Dict[str, Any]]:
        """Execute web search"""
        pass
    
    @abstractmethod
    async def get_page_content(self, url: str) -> str:
        """Fetch page content"""
        pass
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return search capabilities"""
        return {
            "search_types": ["web", "news", "academic"],
            "max_results": 100,
            "features": ["snippets", "relevance_scoring"]
        }
```

### Using Plugins in Theodore

#### 1. **Installing a Plugin**

```bash
# From GitHub
theodore plugin install github:user/theodore-mcp-websearch

# From PyPI
theodore plugin install theodore-plugin-websearch

# From local directory
theodore plugin install ./my-custom-plugin

# With configuration
theodore plugin install github:user/theodore-mcp-websearch \
  --config api_key=YOUR_KEY \
  --config max_results=20
```

#### 2. **Plugin Discovery & Registration**

```python
# theodore/plugins/manager.py
class PluginManager:
    def install_plugin(self, source: str, config: Dict = None):
        """Install a plugin from source"""
        
        # 1. Download/clone plugin
        plugin_path = self._download_plugin(source)
        
        # 2. Load metadata
        metadata = self._load_plugin_metadata(plugin_path)
        
        # 3. Install dependencies
        self._install_dependencies(metadata["dependencies"])
        
        # 4. Register plugin
        plugin_class = self._load_plugin_class(plugin_path, metadata)
        plugin_instance = plugin_class()
        
        # 5. Initialize with config
        plugin_instance.initialize(config or {})
        
        # 6. Register provided interfaces
        for interface, implementation in plugin_instance.get_provided_interfaces().items():
            self.registry.register(interface, implementation)
        
        # 7. Save plugin info
        self._save_plugin_info(metadata["name"], {
            "source": source,
            "version": metadata["version"],
            "config": config,
            "path": plugin_path
        })
```

#### 3. **Using Plugins in Commands**

```python
# theodore/cli/commands/research.py
@click.command()
@click.option('--use-web-search', is_flag=True, help='Enable web search')
def research(company_name, website, use_web_search):
    """Research a company"""
    
    # Get core services
    scraper = registry.get(ScraperPort)
    ai_provider = registry.get(AIProviderPort)
    storage = registry.get(StoragePort)
    
    # Get optional web search if available and requested
    web_search = None
    if use_web_search:
        try:
            web_search = registry.get(WebSearchPort)
        except ServiceNotFound:
            click.echo("Warning: No web search plugin installed")
    
    # Create use case with optional web search
    use_case = ResearchCompanyUseCase(
        scraper=scraper,
        ai_provider=ai_provider,
        storage=storage,
        web_search=web_search  # Optional enhancement
    )
```

### Example Plugin Implementations

#### 1. **Perplexity Search Plugin**

```python
# theodore-plugin-perplexity/src/plugin.py
class PerplexitySearchPlugin(Plugin):
    """Perplexity AI search integration"""
    
    def get_provided_interfaces(self) -> Dict[Type, Type]:
        return {
            WebSearchPort: PerplexitySearchProvider,
            AIProviderPort: PerplexityAIProvider  # Also provides AI analysis
        }
```

#### 2. **Playwright Scraper Plugin**

```python
# theodore-plugin-playwright/src/plugin.py
class PlaywrightScraperPlugin(Plugin):
    """Advanced scraping with Playwright"""
    
    def get_provided_interfaces(self) -> Dict[Type, Type]:
        return {
            ScraperPort: PlaywrightScraper
        }
    
    def initialize(self, config):
        # Install browser if needed
        if config.get("install_browsers", True):
            subprocess.run(["playwright", "install", "chromium"])
```

#### 3. **PostgreSQL Storage Plugin**

```python
# theodore-plugin-postgres/src/plugin.py
class PostgreSQLPlugin(Plugin):
    """PostgreSQL storage backend"""
    
    def get_provided_interfaces(self) -> Dict[Type, Type]:
        return {
            StoragePort: PostgreSQLStorage,
            CachePort: PostgreSQLCache
        }
```

### Plugin Development Guide

#### Creating a New Plugin

```bash
# Use Theodore plugin template
theodore plugin create my-awesome-plugin \
  --template=websearch \
  --author="Your Name"

# This creates:
my-awesome-plugin/
├── plugin.yaml
├── pyproject.toml
├── README.md
├── src/
│   ├── __init__.py
│   ├── plugin.py
│   └── provider.py
├── tests/
│   └── test_plugin.py
└── examples/
    └── usage.py
```

#### Plugin Testing

```python
# tests/test_plugin.py
import pytest
from theodore.plugins.testing import PluginTestCase

class TestMCPWebSearchPlugin(PluginTestCase):
    plugin_class = MCPWebSearchPlugin
    
    @pytest.mark.asyncio
    async def test_search_functionality(self):
        # Initialize plugin
        plugin = self.create_plugin({
            "api_key": "test-key"
        })
        
        # Get provider
        search_provider = plugin.get_provided_interfaces()[WebSearchPort]
        
        # Test search
        results = await search_provider.search("Theodore AI company")
        
        assert len(results) > 0
        assert "title" in results[0]
```

### Plugin Marketplace

```bash
# Browse available plugins
theodore plugin search websearch

# Show plugin details
theodore plugin info theodore-mcp-websearch

# List installed plugins
theodore plugin list

# Update plugin
theodore plugin update theodore-mcp-websearch

# Remove plugin
theodore plugin remove theodore-mcp-websearch
```

### Advanced Plugin Features

#### 1. **Plugin Dependencies**
```yaml
# Plugin can depend on other plugins
requires_plugins:
  - theodore-plugin-cache>=1.0.0
  - theodore-plugin-auth>=2.0.0
```

#### 2. **Plugin Hooks**
```python
class AdvancedPlugin(Plugin):
    def get_hooks(self) -> Dict[str, Callable]:
        return {
            "before_research": self.pre_process,
            "after_research": self.post_process,
            "on_error": self.handle_error
        }
```

#### 3. **Plugin Configuration UI**
```python
def get_config_schema(self) -> Dict:
    return {
        "type": "object",
        "properties": {
            "api_key": {
                "type": "string",
                "description": "API key",
                "ui:widget": "password"  # Special UI hint
            }
        }
    }
```

This plugin system makes Theodore v2 extremely extensible while maintaining clean architecture principles.