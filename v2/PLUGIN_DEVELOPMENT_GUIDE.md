# Theodore v2 Plugin Development Guide

## 🚀 Quick Start

### Creating Your First Plugin

```bash
# 1. Create plugin from template
theodore plugin create my-websearch --template=websearch

# 2. Navigate to plugin directory
cd my-websearch

# 3. Install development dependencies
poetry install

# 4. Run tests
pytest

# 5. Install locally for testing
theodore plugin install .
```

## 📋 Plugin Types & Examples

### 1. Web Search Plugin (MCP-based)

```python
# theodore-mcp-websearch/src/plugin.py
from theodore.plugins.base import Plugin
from theodore.core.interfaces import WebSearchPort
from mcp import MCPServer, MCPClient
import asyncio

class MCPWebSearchPlugin(Plugin):
    """Web search using Model Context Protocol"""
    
    @property
    def name(self) -> str:
        return "mcp-websearch"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> None:
        # Start MCP server for web search
        self.mcp_server = MCPServer(
            name="websearch",
            version="1.0.0",
            capabilities=["search", "fetch"]
        )
        
        # Register search handler
        @self.mcp_server.handler("search")
        async def handle_search(query: str, **kwargs):
            # Implement search logic
            results = await self._perform_search(query, **kwargs)
            return {"results": results}
        
        # Start server
        self.mcp_server.start()
    
    def get_provided_interfaces(self) -> Dict[Type, Type]:
        return {
            WebSearchPort: MCPSearchProvider
        }

class MCPSearchProvider(WebSearchPort):
    """MCP-based search provider"""
    
    def __init__(self, mcp_server):
        self.client = MCPClient(mcp_server)
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        response = await self.client.call("search", {
            "query": query,
            "num_results": num_results
        })
        return response["results"]
```

### 2. AI Provider Plugin

```python
# theodore-plugin-anthropic/src/plugin.py
from theodore.plugins.base import Plugin
from theodore.core.interfaces import AIProviderPort
import anthropic

class AnthropicPlugin(Plugin):
    """Anthropic Claude AI provider"""
    
    @property
    def name(self) -> str:
        return "anthropic-ai"
    
    def initialize(self, config: Dict[str, Any]) -> None:
        self.api_key = config.get("api_key")
        if not self.api_key:
            raise ValueError("Anthropic API key required")
    
    def get_provided_interfaces(self) -> Dict[Type, Type]:
        return {
            AIProviderPort: AnthropicAIProvider
        }

class AnthropicAIProvider(AIProviderPort):
    """Anthropic AI implementation"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def analyze_content(self, content: str, prompt: str) -> str:
        message = await self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\nContent:\n{content}"
            }]
        )
        return message.content[0].text
    
    async def generate_embedding(self, text: str) -> List[float]:
        # Anthropic doesn't provide embeddings, use a different service
        raise NotImplementedError("Use a dedicated embedding service")
```

### 3. Storage Backend Plugin

```python
# theodore-plugin-elasticsearch/src/plugin.py
from theodore.plugins.base import Plugin
from theodore.core.interfaces import StoragePort
from elasticsearch import AsyncElasticsearch

class ElasticsearchPlugin(Plugin):
    """Elasticsearch storage backend"""
    
    @property
    def name(self) -> str:
        return "elasticsearch-storage"
    
    def initialize(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.client = AsyncElasticsearch(
            hosts=config.get("hosts", ["localhost:9200"]),
            api_key=config.get("api_key")
        )
    
    def get_provided_interfaces(self) -> Dict[Type, Type]:
        return {
            StoragePort: ElasticsearchStorage
        }

class ElasticsearchStorage(StoragePort):
    """Elasticsearch storage implementation"""
    
    def __init__(self, client: AsyncElasticsearch):
        self.client = client
        self.index = "theodore-companies"
    
    async def save_company(self, company: Company) -> str:
        response = await self.client.index(
            index=self.index,
            id=company.id,
            body=company.to_dict()
        )
        return response["_id"]
    
    async def search_similar(self, embedding: List[float], limit: int = 10) -> List[Company]:
        # Elasticsearch KNN search
        response = await self.client.search(
            index=self.index,
            body={
                "knn": {
                    "field": "embedding",
                    "query_vector": embedding,
                    "k": limit,
                    "num_candidates": limit * 10
                }
            }
        )
        
        return [
            Company(**hit["_source"])
            for hit in response["hits"]["hits"]
        ]
```

### 4. Scraper Plugin

```python
# theodore-plugin-browserless/src/plugin.py
from theodore.plugins.base import Plugin
from theodore.core.interfaces import ScraperPort
import httpx

class BrowserlessPlugin(Plugin):
    """Browserless.io scraping service"""
    
    @property
    def name(self) -> str:
        return "browserless-scraper"
    
    def initialize(self, config: Dict[str, Any]) -> None:
        self.api_key = config["api_key"]
        self.endpoint = config.get("endpoint", "https://chrome.browserless.io")
    
    def get_provided_interfaces(self) -> Dict[Type, Type]:
        return {
            ScraperPort: BrowserlessScraper
        }

class BrowserlessScraper(ScraperPort):
    """Browserless scraping implementation"""
    
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint
        self.client = httpx.AsyncClient()
    
    async def scrape_pages(self, urls: List[str], options: Dict = None) -> Dict[str, str]:
        results = {}
        
        for url in urls:
            response = await self.client.post(
                f"{self.endpoint}/content",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "url": url,
                    "waitFor": options.get("wait_for", 3000),
                    "screenshot": False,
                    "elements": [{
                        "selector": "body",
                        "timeout": 30000
                    }]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                results[url] = data["data"][0]["text"]
            
        return results
```

## 🔧 Plugin Structure

### Required Files

```bash
my-plugin/
├── plugin.yaml              # Plugin metadata (required)
├── pyproject.toml          # Python package info (required)
├── README.md               # Documentation (required)
├── LICENSE                 # License file (recommended)
├── src/
│   ├── __init__.py
│   ├── plugin.py          # Main plugin class (required)
│   └── providers.py       # Interface implementations
├── tests/
│   ├── __init__.py
│   └── test_plugin.py     # Tests (recommended)
├── examples/
│   ├── basic_usage.py
│   └── config.yaml
└── docs/
    └── configuration.md
```

### plugin.yaml Schema

```yaml
# Metadata
name: my-awesome-plugin
version: 1.0.0
description: Brief description of what your plugin does
author: Your Name
email: your.email@example.com
license: MIT
homepage: https://github.com/yourusername/theodore-plugin-awesome
repository: https://github.com/yourusername/theodore-plugin-awesome

# Entry point
entry_point: MyAwesomePlugin  # Class name in plugin.py

# What this plugin provides
provides:
  - interface: WebSearchPort
    implementation: MyWebSearchProvider
  - interface: CachePort
    implementation: MyCache

# Dependencies
requires:
  theodore: ">=2.0.0"
  python: ">=3.11"

dependencies:
  - httpx>=0.24.0
  - beautifulsoup4>=4.12.0

# Optional: Require other plugins
requires_plugins:
  - theodore-plugin-cache>=1.0.0

# Configuration schema (JSON Schema)
config_schema:
  type: object
  properties:
    api_key:
      type: string
      description: API key for the service
      ui:widget: password  # UI hint for config interface
    endpoint:
      type: string
      format: uri
      default: https://api.example.com
    max_retries:
      type: integer
      minimum: 0
      maximum: 10
      default: 3
    cache_ttl:
      type: integer
      description: Cache TTL in seconds
      default: 3600
  required:
    - api_key

# Capabilities (for discovery)
capabilities:
  - web_search
  - news_search
  - image_search
  - local_search

# Tags (for marketplace)
tags:
  - search
  - web
  - api
  - mcp

# System requirements
system_requirements:
  - command: chromium
    optional: true
    install_hint: "Install with: playwright install chromium"
```

## 🎯 Best Practices

### 1. **Follow SOLID Principles**

```python
# Single Responsibility
class WebSearchProvider(WebSearchPort):
    """Only handles web search, nothing else"""
    
    async def search(self, query: str, **kwargs) -> List[Dict]:
        # Just search, don't parse or cache
        return await self._search_api(query, **kwargs)

# Separate concerns
class SearchResultParser:
    """Only handles parsing search results"""
    
    def parse(self, raw_results: Dict) -> List[SearchResult]:
        # Just parse, don't search
        pass
```

### 2. **Async First**

```python
# Always use async/await for I/O operations
class MyPlugin(Plugin):
    async def initialize_async(self, config: Dict[str, Any]) -> None:
        """Async initialization for I/O operations"""
        self.client = await self._create_client(config)
        await self.client.test_connection()
```

### 3. **Proper Error Handling**

```python
from theodore.plugins.exceptions import PluginError, ConfigurationError

class MyPlugin(Plugin):
    def initialize(self, config: Dict[str, Any]) -> None:
        if "api_key" not in config:
            raise ConfigurationError("API key is required")
        
        try:
            self.client = MyClient(config["api_key"])
        except Exception as e:
            raise PluginError(f"Failed to initialize client: {e}")
```

### 4. **Configuration Validation**

```python
from pydantic import BaseModel, Field, validator

class MyPluginConfig(BaseModel):
    api_key: str = Field(..., min_length=20)
    endpoint: str = Field(default="https://api.example.com")
    timeout: int = Field(default=30, ge=1, le=300)
    
    @validator("endpoint")
    def validate_endpoint(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("Endpoint must be a valid URL")
        return v

class MyPlugin(Plugin):
    def initialize(self, config: Dict[str, Any]) -> None:
        # Validate configuration
        self.config = MyPluginConfig(**config)
```

### 5. **Logging & Monitoring**

```python
import structlog
from theodore.plugins.telemetry import PluginMetrics

class MyPlugin(Plugin):
    def initialize(self, config: Dict[str, Any]) -> None:
        self.logger = structlog.get_logger().bind(
            plugin=self.name,
            version=self.version
        )
        self.metrics = PluginMetrics(self.name)
        
        self.logger.info("Plugin initialized", config_keys=list(config.keys()))
    
    async def search(self, query: str) -> List[Dict]:
        with self.metrics.timer("search_duration"):
            self.logger.info("Executing search", query=query)
            try:
                results = await self._search(query)
                self.metrics.increment("search_success")
                return results
            except Exception as e:
                self.metrics.increment("search_error")
                self.logger.error("Search failed", error=str(e))
                raise
```

### 6. **Testing**

```python
# tests/test_plugin.py
import pytest
from unittest.mock import Mock, AsyncMock
from theodore.plugins.testing import PluginTestCase

class TestMyPlugin(PluginTestCase):
    plugin_class = MyPlugin
    
    @pytest.fixture
    def mock_config(self):
        return {
            "api_key": "test-key-12345",
            "endpoint": "https://test.example.com"
        }
    
    @pytest.fixture
    def mock_http_client(self, mocker):
        client = Mock()
        client.get = AsyncMock()
        mocker.patch("httpx.AsyncClient", return_value=client)
        return client
    
    @pytest.mark.asyncio
    async def test_search_success(self, mock_config, mock_http_client):
        # Arrange
        plugin = self.create_plugin(mock_config)
        mock_http_client.get.return_value.json.return_value = {
            "results": [{"title": "Test", "url": "https://test.com"}]
        }
        
        # Act
        provider = plugin.get_provided_interfaces()[WebSearchPort]
        results = await provider.search("test query")
        
        # Assert
        assert len(results) == 1
        assert results[0]["title"] == "Test"
        mock_http_client.get.assert_called_once()
```

## 🚢 Publishing Your Plugin

### 1. **Prepare for Release**

```bash
# Update version
poetry version patch  # or minor/major

# Run tests
pytest --cov=src

# Build package
poetry build

# Check package
twine check dist/*
```

### 2. **Publish to PyPI**

```bash
# Publish to PyPI
poetry publish

# Or using twine
twine upload dist/*
```

### 3. **Submit to Theodore Marketplace**

```yaml
# marketplace.yaml
listing:
  name: theodore-plugin-awesome
  category: search
  featured: false
  pricing: free  # or paid
  support_url: https://github.com/you/plugin/issues
  documentation_url: https://github.com/you/plugin/wiki
  
  screenshots:
    - url: https://example.com/screenshot1.png
      caption: Search results
    - url: https://example.com/screenshot2.png
      caption: Configuration

  compatibility:
    theodore_min_version: "2.0.0"
    theodore_max_version: "3.0.0"
    platforms:
      - linux
      - macos
      - windows
```

### 4. **GitHub Release**

```bash
# Tag release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Create GitHub release with:
# - Changelog
# - Installation instructions
# - Binary artifacts (if any)
```

## 🔍 Plugin Discovery

### How Theodore Finds Plugins

1. **PyPI Search**
   ```bash
   theodore plugin search theodore-plugin-*
   ```

2. **GitHub Topics**
   ```
   topic:theodore-plugin
   topic:theodore-v2
   ```

3. **Official Registry**
   ```
   https://plugins.theodore.ai/registry.json
   ```

4. **Local Discovery**
   ```bash
   theodore plugin scan ./my-plugins/
   ```

## 🛠️ Advanced Topics

### Dynamic Loading

```python
class PluginLoader:
    """Advanced plugin loading with hot reload"""
    
    def load_plugin(self, path: Path) -> Plugin:
        # Dynamic import
        spec = importlib.util.spec_from_file_location(
            "plugin_module", 
            path / "src" / "plugin.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin class
        for item_name in dir(module):
            item = getattr(module, item_name)
            if isinstance(item, type) and issubclass(item, Plugin):
                return item()
```

### Plugin Communication

```python
# Plugins can communicate via events
class MyPlugin(Plugin):
    def initialize(self, config: Dict[str, Any]) -> None:
        # Subscribe to events
        event_bus.subscribe("company.researched", self.on_company_researched)
    
    async def on_company_researched(self, event: Event):
        # React to other plugins' events
        company_id = event.data["company_id"]
        await self.enrich_company_data(company_id)
```

### Performance Monitoring

```python
from theodore.plugins.profiling import profile_method

class MyPlugin(Plugin):
    @profile_method
    async def expensive_operation(self):
        # This method will be automatically profiled
        pass
```

This guide provides everything needed to create powerful plugins for Theodore v2!