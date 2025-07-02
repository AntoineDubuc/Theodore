# Theodore v2: Comprehensive Upgrade & Modularization Plan

## 🎯 Vision & Goals

**Theodore v2** will be a **CLI-first, plugin-based company intelligence system** built on clean architecture principles, designed for:

- **Modularity**: Loosely coupled components with clear boundaries
- **Scalability**: Queue-based processing, horizontal scaling support
- **Extensibility**: Rich plugin ecosystem for scrapers, AI providers, storage
- **Maintainability**: Clean code, comprehensive testing, clear documentation
- **CLI-First**: Powerful command-line interface with optional UI attachment

## 📐 Current Architecture Analysis

### Current Issues

1. **Tight Coupling**
   - Components directly instantiate other components
   - No dependency injection or inversion of control
   - Business logic mixed with infrastructure

2. **Missing Abstractions**
   - No interface definitions
   - Services communicate through concrete implementations
   - Plugin support impossible without major refactoring

3. **State Management Issues**
   - Global state in web layer
   - File-based progress tracking
   - Not suitable for distributed systems

4. **Scalability Constraints**
   - Single process architecture
   - Blocking I/O operations
   - Hard-coded resource limits

## 🏗️ Proposed Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      CLI Interface                         │
│                   theodore-cli (Click)                     │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│                  Application Core                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   Commands  │  │   Use Cases  │  │  Domain Models │  │
│  │  (Research) │  │  (Business)  │  │   (Entities)   │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│                    Port Layer                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Scraper    │  │      AI      │  │    Storage     │  │
│  │  Interface  │  │  Interface   │  │   Interface    │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│                  Adapter Layer                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Crawl4AI   │  │   Bedrock    │  │    Pinecone    │  │
│  │  Selenium   │  │   Gemini     │  │   PostgreSQL   │  │
│  │  Playwright │  │   OpenAI     │  │   Elasticsearch│  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│                  Infrastructure                            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   Events    │  │    Queue     │  │     Cache      │  │
│  │    Bus      │  │   (Celery)   │  │    (Redis)     │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## 📁 Implementation Plan

### Phase 1: Core Foundation (Weeks 1-2)

#### 1.1 Project Structure

```bash
theodore-v2/
├── src/
│   ├── theodore/
│   │   ├── __init__.py
│   │   ├── __version__.py
│   │   ├── cli/                    # CLI entry points
│   │   │   ├── __init__.py
│   │   │   ├── main.py            # Main CLI app
│   │   │   ├── commands/          # CLI commands
│   │   │   │   ├── research.py
│   │   │   │   ├── discover.py
│   │   │   │   ├── config.py
│   │   │   │   └── plugins.py
│   │   │   └── formatters/        # Output formatters
│   │   ├── core/                  # Business logic
│   │   │   ├── domain/            # Domain models
│   │   │   │   ├── company.py
│   │   │   │   ├── research.py
│   │   │   │   └── intelligence.py
│   │   │   ├── use_cases/         # Business operations
│   │   │   │   ├── research_company.py
│   │   │   │   ├── discover_similar.py
│   │   │   │   └── analyze_intelligence.py
│   │   │   └── interfaces/        # Port definitions
│   │   │       ├── scraper.py
│   │   │       ├── ai_provider.py
│   │   │       ├── storage.py
│   │   │       └── cache.py
│   │   ├── adapters/              # Interface implementations
│   │   │   ├── scrapers/
│   │   │   ├── ai_providers/
│   │   │   ├── storage/
│   │   │   └── cache/
│   │   ├── infrastructure/        # Technical services
│   │   │   ├── config.py
│   │   │   ├── events.py
│   │   │   ├── queue.py
│   │   │   └── logging.py
│   │   └── plugins/               # Plugin system
│   │       ├── manager.py
│   │       ├── registry.py
│   │       └── base.py
├── tests/
├── plugins/                       # External plugins
├── config/
│   ├── default.yaml
│   └── schemas/
├── docs/
└── pyproject.toml                # Modern Python packaging
```

#### 1.2 Domain Models (Clean Entities)

```python
# src/theodore/core/domain/company.py
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class CompanyStage(Enum):
    SEED = "seed"
    EARLY = "early"
    GROWTH = "growth"
    MATURE = "mature"
    ENTERPRISE = "enterprise"

@dataclass(frozen=True)
class Company:
    """Immutable company entity"""
    id: str
    name: str
    website: str
    industry: Optional[str] = None
    business_model: Optional[str] = None
    stage: Optional[CompanyStage] = None
    founding_year: Optional[int] = None
    employee_count: Optional[str] = None
    location: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class ResearchResult:
    """Research outcome for a company"""
    company_id: str
    scraped_pages: List[str]
    raw_content: Dict[str, str]
    extracted_data: Dict[str, any]
    intelligence_summary: str
    confidence_scores: Dict[str, float]
    processing_time: float
    timestamp: datetime
    
@dataclass
class CompanyIntelligence:
    """Analyzed intelligence about a company"""
    company: Company
    description: str
    value_proposition: str
    target_market: str
    competitive_advantages: List[str]
    pain_points: List[str]
    technology_stack: List[str]
    key_personnel: List[Dict[str, str]]
    financial_indicators: Dict[str, any]
    market_position: str
    growth_trajectory: str
    vector_embedding: Optional[List[float]] = None
```

#### 1.3 Port Interfaces (Hexagonal Architecture)

```python
# src/theodore/core/interfaces/scraper.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from ..domain.company import Company

class ScraperPort(ABC):
    """Port for web scraping operations"""
    
    @abstractmethod
    async def discover_pages(self, website: str, max_pages: int = 50) -> List[str]:
        """Discover available pages on a website"""
        pass
    
    @abstractmethod
    async def scrape_pages(self, urls: List[str], options: Dict = None) -> Dict[str, str]:
        """Scrape content from multiple pages"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, any]:
        """Return scraper capabilities and limitations"""
        pass

# src/theodore/core/interfaces/ai_provider.py
class AIProviderPort(ABC):
    """Port for AI analysis operations"""
    
    @abstractmethod
    async def analyze_content(self, content: str, prompt: str) -> str:
        """Analyze content with given prompt"""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for text"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, any]:
        """Return model capabilities and costs"""
        pass

# src/theodore/core/interfaces/storage.py  
class StoragePort(ABC):
    """Port for data persistence"""
    
    @abstractmethod
    async def save_company(self, company: Company) -> str:
        """Save company data"""
        pass
    
    @abstractmethod
    async def find_company(self, company_id: str) -> Optional[Company]:
        """Retrieve company by ID"""
        pass
    
    @abstractmethod
    async def search_similar(self, embedding: List[float], limit: int = 10) -> List[Company]:
        """Find similar companies by vector similarity"""
        pass
```

#### 1.4 Use Cases (Business Logic)

```python
# src/theodore/core/use_cases/research_company.py
from dataclasses import dataclass
from typing import Optional
from ..interfaces import ScraperPort, AIProviderPort, StoragePort
from ..domain.company import Company, ResearchResult

@dataclass
class ResearchCompanyRequest:
    company_name: str
    website: str
    max_pages: int = 50
    deep_analysis: bool = True

class ResearchCompanyUseCase:
    def __init__(self, 
                 scraper: ScraperPort,
                 ai_provider: AIProviderPort,
                 storage: StoragePort):
        self.scraper = scraper
        self.ai_provider = ai_provider
        self.storage = storage
    
    async def execute(self, request: ResearchCompanyRequest) -> ResearchResult:
        # 1. Check if company exists
        existing = await self.storage.find_by_website(request.website)
        if existing and not request.force_refresh:
            return existing
        
        # 2. Discover pages
        pages = await self.scraper.discover_pages(
            request.website, 
            request.max_pages
        )
        
        # 3. Select relevant pages with AI
        selection_prompt = self._build_selection_prompt(pages)
        selected_urls = await self.ai_provider.analyze_content(
            "\n".join(pages),
            selection_prompt
        )
        
        # 4. Scrape selected pages
        scraped_content = await self.scraper.scrape_pages(selected_urls)
        
        # 5. Analyze with AI
        analysis = await self._analyze_company(scraped_content)
        
        # 6. Generate embedding
        embedding = await self.ai_provider.generate_embedding(
            analysis.intelligence_summary
        )
        
        # 7. Save to storage
        company = Company(
            name=request.company_name,
            website=request.website,
            **analysis.extracted_data
        )
        await self.storage.save_company(company)
        
        return ResearchResult(
            company_id=company.id,
            scraped_pages=selected_urls,
            raw_content=scraped_content,
            extracted_data=analysis.extracted_data,
            intelligence_summary=analysis.intelligence_summary,
            confidence_scores=analysis.confidence_scores,
            processing_time=analysis.processing_time,
            timestamp=datetime.now()
        )
```

#### 1.5 Plugin System

```python
# src/theodore/plugins/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Type

class Plugin(ABC):
    """Base class for all Theodore plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """List of required dependencies"""
        pass
    
    @abstractmethod
    def get_provided_interfaces(self) -> Dict[Type, Type]:
        """Map of interface to implementation"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration"""
        pass

# src/theodore/plugins/manager.py
class PluginManager:
    """Manages plugin lifecycle and registration"""
    
    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self.plugins = {}
        self.registry = ServiceRegistry()
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins"""
        plugins = []
        for entry in self.plugin_dir.iterdir():
            if entry.is_dir() and (entry / "plugin.yaml").exists():
                plugins.append(entry.name)
        return plugins
    
    def load_plugin(self, plugin_name: str) -> None:
        """Load and register a plugin"""
        plugin_path = self.plugin_dir / plugin_name
        config = self._load_plugin_config(plugin_path)
        
        # Dynamic import
        module = importlib.import_module(f"plugins.{plugin_name}")
        plugin_class = getattr(module, config["entry_point"])
        
        # Instantiate and initialize
        plugin = plugin_class()
        plugin.initialize(config.get("config", {}))
        
        # Register provided interfaces
        for interface, implementation in plugin.get_provided_interfaces().items():
            self.registry.register(interface, implementation)
        
        self.plugins[plugin_name] = plugin
```

#### 1.6 CLI Implementation

```python
# src/theodore/cli/main.py
import click
from ..infrastructure.config import load_config
from ..plugins.manager import PluginManager
from ..core.use_cases import ResearchCompanyUseCase

@click.group()
@click.option('--config', '-c', default='config/default.yaml', help='Configuration file')
@click.option('--plugins-dir', '-p', default='plugins', help='Plugins directory')
@click.pass_context
def cli(ctx, config, plugins_dir):
    """Theodore - AI Company Intelligence System"""
    ctx.ensure_object(dict)
    
    # Load configuration
    ctx.obj['config'] = load_config(config)
    
    # Initialize plugin system
    plugin_manager = PluginManager(Path(plugins_dir))
    plugin_manager.discover_and_load_plugins()
    ctx.obj['registry'] = plugin_manager.registry

@cli.command()
@click.argument('company_name')
@click.argument('website')
@click.option('--max-pages', '-m', default=50, help='Maximum pages to scrape')
@click.option('--output', '-o', type=click.Choice(['json', 'yaml', 'table']), default='table')
@click.pass_context
def research(ctx, company_name, website, max_pages, output):
    """Research a company and extract intelligence"""
    registry = ctx.obj['registry']
    
    # Get implementations from registry
    scraper = registry.get(ScraperPort)
    ai_provider = registry.get(AIProviderPort)
    storage = registry.get(StoragePort)
    
    # Execute use case
    use_case = ResearchCompanyUseCase(scraper, ai_provider, storage)
    result = asyncio.run(use_case.execute(
        ResearchCompanyRequest(
            company_name=company_name,
            website=website,
            max_pages=max_pages
        )
    ))
    
    # Format output
    formatter = get_formatter(output)
    click.echo(formatter.format(result))

@cli.command()
@click.argument('company_name')
@click.option('--limit', '-l', default=10, help='Number of similar companies')
@click.pass_context
def discover(ctx, company_name, limit):
    """Discover similar companies"""
    # Implementation...
    pass

@cli.group()
def plugin():
    """Manage plugins"""
    pass

@plugin.command('list')
@click.pass_context
def list_plugins(ctx):
    """List available plugins"""
    # Implementation...
    pass
```

### Phase 2: Core Adapters (Weeks 3-4)

#### 2.1 Scraper Adapters

```python
# src/theodore/adapters/scrapers/crawl4ai_adapter.py
from crawl4ai import AsyncWebCrawler
from ...core.interfaces import ScraperPort

class Crawl4AIAdapter(ScraperPort):
    """Adapter for Crawl4AI scraping"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.crawler = None
    
    async def discover_pages(self, website: str, max_pages: int = 50) -> List[str]:
        async with AsyncWebCrawler() as crawler:
            # Implementation using Crawl4AI
            result = await crawler.arun(
                url=website,
                word_count_threshold=self.config.get('word_threshold', 10),
                exclude_external_links=True,
                screenshot=False
            )
            # Parse and return discovered URLs
            return self._extract_urls(result)
    
    async def scrape_pages(self, urls: List[str], options: Dict = None) -> Dict[str, str]:
        results = {}
        async with AsyncWebCrawler() as crawler:
            for url in urls:
                result = await crawler.arun(url=url, **options)
                results[url] = result.text
        return results

# plugins/playwright_scraper/adapter.py
class PlaywrightScraperAdapter(ScraperPort):
    """Alternative scraper using Playwright"""
    # Implementation...
```

#### 2.2 AI Provider Adapters

```python
# src/theodore/adapters/ai_providers/bedrock_adapter.py
import boto3
from ...core.interfaces import AIProviderPort

class BedrockAdapter(AIProviderPort):
    """AWS Bedrock AI adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=config['region'],
            aws_access_key_id=config['access_key'],
            aws_secret_access_key=config['secret_key']
        )
        self.model_id = config.get('model_id', 'amazon.nova-pro-v1:0')
    
    async def analyze_content(self, content: str, prompt: str) -> str:
        response = await self._invoke_model({
            "prompt": f"{prompt}\n\nContent:\n{content}",
            "max_tokens": 4096,
            "temperature": 0.7
        })
        return response['completion']
    
    async def generate_embedding(self, text: str) -> List[float]:
        # Implementation for embeddings
        pass
```

#### 2.3 Storage Adapters

```python
# src/theodore/adapters/storage/pinecone_adapter.py
from pinecone import Pinecone
from ...core.interfaces import StoragePort

class PineconeAdapter(StoragePort):
    """Pinecone vector database adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        self.pc = Pinecone(api_key=config['api_key'])
        self.index = self.pc.Index(config['index_name'])
    
    async def save_company(self, company: Company) -> str:
        # Convert to vector format and upsert
        vector_data = {
            "id": company.id,
            "values": company.vector_embedding,
            "metadata": company.to_dict()
        }
        self.index.upsert([vector_data])
        return company.id
```

### Phase 3: Infrastructure & Events (Weeks 5-6)

#### 3.1 Event System

```python
# src/theodore/infrastructure/events.py
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class Event:
    """Base event class"""
    id: str
    timestamp: datetime
    type: str
    data: Dict[str, Any]

class EventBus:
    """Simple event bus for decoupled communication"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._queue = asyncio.Queue()
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def publish(self, event: Event) -> None:
        await self._queue.put(event)
    
    async def process_events(self) -> None:
        while True:
            event = await self._queue.get()
            handlers = self._handlers.get(event.type, [])
            
            await asyncio.gather(*[
                handler(event) for handler in handlers
            ])

# Usage in use cases
class ResearchCompanyUseCase:
    def __init__(self, event_bus: EventBus, ...):
        self.event_bus = event_bus
    
    async def execute(self, request):
        # ... research logic ...
        
        # Publish event
        await self.event_bus.publish(Event(
            id=str(uuid4()),
            timestamp=datetime.now(),
            type="company.researched",
            data={
                "company_id": company.id,
                "company_name": company.name,
                "pages_scraped": len(scraped_pages)
            }
        ))
```

#### 3.2 Queue System

```python
# src/theodore/infrastructure/queue.py
from celery import Celery
from ..core.use_cases import ResearchCompanyUseCase

app = Celery('theodore', broker='redis://localhost:6379')

@app.task
def research_company_task(company_name: str, website: str):
    """Background task for company research"""
    # Get dependencies from registry
    scraper = get_service(ScraperPort)
    ai_provider = get_service(AIProviderPort)
    storage = get_service(StoragePort)
    
    # Execute use case
    use_case = ResearchCompanyUseCase(scraper, ai_provider, storage)
    result = asyncio.run(use_case.execute(
        ResearchCompanyRequest(company_name, website)
    ))
    
    return result.to_dict()

# CLI integration
@cli.command()
@click.option('--async', 'is_async', is_flag=True, help='Run asynchronously')
def research(company_name, website, is_async):
    if is_async:
        task = research_company_task.delay(company_name, website)
        click.echo(f"Task queued: {task.id}")
    else:
        # Synchronous execution
        pass
```

#### 3.3 Configuration System

```python
# src/theodore/infrastructure/config.py
from pydantic import BaseSettings, BaseModel
from typing import Dict, Any, Optional
import yaml

class ScraperConfig(BaseModel):
    type: str = "crawl4ai"
    max_pages: int = 50
    concurrent_limit: int = 10
    timeout: int = 30
    
class AIProviderConfig(BaseModel):
    type: str = "bedrock"
    model: str = "amazon.nova-pro-v1:0"
    max_tokens: int = 4096
    temperature: float = 0.7

class StorageConfig(BaseModel):
    type: str = "pinecone"
    index_name: str = "theodore-companies"

class TheodoreConfig(BaseSettings):
    scraper: ScraperConfig = ScraperConfig()
    ai_provider: AIProviderConfig = AIProviderConfig()
    storage: StorageConfig = StorageConfig()
    plugins: Dict[str, Dict[str, Any]] = {}
    
    class Config:
        env_prefix = "THEODORE_"
        env_nested_delimiter = "__"

def load_config(config_file: str) -> TheodoreConfig:
    """Load configuration from file and environment"""
    with open(config_file) as f:
        config_data = yaml.safe_load(f)
    
    # Merge with environment variables
    return TheodoreConfig(**config_data)
```

### Phase 4: Testing & Quality (Weeks 7-8)

#### 4.1 Unit Tests

```python
# tests/unit/core/use_cases/test_research_company.py
import pytest
from unittest.mock import Mock, AsyncMock
from theodore.core.use_cases import ResearchCompanyUseCase

@pytest.fixture
def mock_scraper():
    scraper = Mock(ScraperPort)
    scraper.discover_pages = AsyncMock(return_value=[
        "https://example.com/about",
        "https://example.com/contact"
    ])
    scraper.scrape_pages = AsyncMock(return_value={
        "https://example.com/about": "About us content..."
    })
    return scraper

@pytest.fixture
def mock_ai_provider():
    ai = Mock(AIProviderPort)
    ai.analyze_content = AsyncMock(return_value="Analysis result")
    ai.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    return ai

@pytest.mark.asyncio
async def test_research_company(mock_scraper, mock_ai_provider, mock_storage):
    use_case = ResearchCompanyUseCase(
        mock_scraper, 
        mock_ai_provider, 
        mock_storage
    )
    
    result = await use_case.execute(
        ResearchCompanyRequest(
            company_name="Test Corp",
            website="https://example.com"
        )
    )
    
    assert result.company_id is not None
    assert len(result.scraped_pages) > 0
    mock_scraper.discover_pages.assert_called_once()
    mock_ai_provider.analyze_content.assert_called()
```

#### 4.2 Integration Tests

```python
# tests/integration/test_cli.py
from click.testing import CliRunner
from theodore.cli.main import cli

def test_research_command():
    runner = CliRunner()
    result = runner.invoke(cli, [
        'research', 
        'Test Company', 
        'https://example.com',
        '--output', 'json'
    ])
    
    assert result.exit_code == 0
    assert 'Test Company' in result.output
```

#### 4.3 Plugin Tests

```python
# tests/plugins/test_plugin_loading.py
def test_plugin_discovery(tmp_path):
    # Create test plugin structure
    plugin_dir = tmp_path / "test_plugin"
    plugin_dir.mkdir()
    
    config = {
        "name": "test_plugin",
        "version": "1.0.0",
        "entry_point": "TestPlugin"
    }
    
    with open(plugin_dir / "plugin.yaml", "w") as f:
        yaml.dump(config, f)
    
    manager = PluginManager(tmp_path)
    plugins = manager.discover_plugins()
    
    assert "test_plugin" in plugins
```

### Phase 5: Migration & Deployment (Weeks 9-10)

#### 5.1 Data Migration

```python
# scripts/migrate_v1_to_v2.py
import asyncio
from theodore_v1 import PineconeClient as V1Client
from theodore.adapters.storage import PineconeAdapter

async def migrate_companies():
    """Migrate company data from v1 to v2"""
    v1_client = V1Client()
    v2_storage = PineconeAdapter(config)
    
    # Fetch all v1 companies
    v1_companies = v1_client.get_all_companies()
    
    for v1_company in v1_companies:
        # Transform to v2 format
        v2_company = transform_company(v1_company)
        
        # Save to v2 storage
        await v2_storage.save_company(v2_company)
        
        print(f"Migrated: {v2_company.name}")
```

#### 5.2 Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application
COPY src/ ./src/
COPY config/ ./config/
COPY plugins/ ./plugins/

# Set entrypoint
ENTRYPOINT ["python", "-m", "theodore.cli.main"]
```

#### 5.3 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  theodore:
    build: .
    environment:
      - THEODORE_STORAGE__TYPE=pinecone
      - THEODORE_AI_PROVIDER__TYPE=bedrock
    volumes:
      - ./config:/app/config
      - ./plugins:/app/plugins
    depends_on:
      - redis
      
  worker:
    build: .
    command: celery -A theodore.infrastructure.queue worker
    environment:
      - CELERY_BROKER_URL=redis://redis:6379
    depends_on:
      - redis
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Phase 6: UI Attachment (Weeks 11-12)

#### 6.1 API Layer

```python
# src/theodore/api/server.py
from fastapi import FastAPI, BackgroundTasks
from ..core.use_cases import ResearchCompanyUseCase

app = FastAPI(title="Theodore API", version="2.0.0")

@app.post("/api/v2/research")
async def research_company(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """Queue company research"""
    task_id = str(uuid4())
    
    background_tasks.add_task(
        execute_research,
        task_id,
        request
    )
    
    return {
        "task_id": task_id,
        "status": "queued"
    }

@app.get("/api/v2/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status and results"""
    # Implementation
    pass

@app.websocket("/ws/progress/{task_id}")
async def progress_websocket(websocket: WebSocket, task_id: str):
    """Real-time progress updates"""
    await websocket.accept()
    
    # Subscribe to task events
    async for event in task_events(task_id):
        await websocket.send_json(event)
```

#### 6.2 CLI with API Mode

```python
# src/theodore/cli/main.py
@cli.command()
@click.option('--api-mode', is_flag=True, help='Start API server')
@click.option('--port', default=8000, help='API port')
def serve(api_mode, port):
    """Start Theodore in server mode"""
    if api_mode:
        import uvicorn
        uvicorn.run(
            "theodore.api.server:app",
            host="0.0.0.0",
            port=port,
            reload=True
        )
```

## 🎯 Migration Strategy

### Phase 1: Parallel Development
- Keep v1 running while building v2
- No breaking changes to v1
- Develop v2 in separate repository

### Phase 2: Feature Parity
- Implement all v1 features in v2
- Extensive testing comparing results
- Performance benchmarking

### Phase 3: Data Migration
- Export all v1 data
- Transform to v2 format
- Import with verification

### Phase 4: Gradual Rollout
- Deploy v2 alongside v1
- Route percentage of traffic to v2
- Monitor for issues

### Phase 5: Complete Migration
- Switch all traffic to v2
- Deprecate v1 endpoints
- Archive v1 codebase

## 📊 Success Metrics

1. **Performance**
   - 50% reduction in research time
   - Support for 10x concurrent operations
   - Sub-second response times for cached data

2. **Scalability**
   - Horizontal scaling to N workers
   - Queue-based load distribution
   - Stateless service architecture

3. **Maintainability**
   - 90%+ test coverage
   - Clear separation of concerns
   - Comprehensive documentation

4. **Extensibility**
   - 10+ community plugins
   - Easy custom adapter creation
   - Plugin marketplace

## 🚀 Next Steps

1. **Set up v2 repository structure**
2. **Implement core domain models**
3. **Create basic CLI framework**
4. **Build first adapter (Crawl4AI)**
5. **Implement research use case**
6. **Add plugin system**
7. **Create comprehensive tests**
8. **Documentation and examples**

## 🏆 Benefits Summary

This architecture provides a solid foundation for Theodore v2 that is:

- **Modular**: Clean boundaries between components
- **Extensible**: Rich plugin ecosystem
- **Scalable**: Queue-based async processing
- **Maintainable**: Clear structure and testing
- **CLI-First**: Powerful command-line interface with optional UI

The clean architecture principles ensure that business logic is separated from infrastructure concerns, making the system flexible and adaptable to changing requirements.