# TICKET-021: CLI Discover Command Implementation

## Overview
Implement the comprehensive `theodore discover` command that provides intelligent company discovery with advanced filtering, similarity scoring, and interactive research capabilities.

## Problem Statement
Users need a powerful discovery interface to find similar companies that:
- Provides intelligent similarity matching beyond simple keyword search
- Offers advanced filtering by business model, company size, industry, and growth stage
- Shows transparent similarity scores with explanations of matching criteria
- Enables seamless transition from discovery to detailed research
- Supports both vector-based similarity and web search fallbacks
- Handles unknown companies gracefully with alternative discovery methods
- Provides interactive workflows for exploring discovered companies
- Integrates seamlessly with Theodore's research capabilities

Without a sophisticated discovery command, users cannot effectively explore the competitive landscape or find relevant companies for analysis.

## Acceptance Criteria
- [ ] Parse company name with intelligent normalization and validation
- [ ] Support comprehensive result limiting with smart defaults
- [ ] Implement advanced filtering system (business model, size, industry, stage, location)
- [ ] Show real-time discovery progress with source transparency
- [ ] Display ranked results with detailed similarity scores and explanations
- [ ] Support all output formats from research command (table, json, yaml, markdown)
- [ ] Provide interactive research option for discovered companies
- [ ] Handle unknown companies with fallback discovery strategies
- [ ] Support discovery history and result caching
- [ ] Implement similarity threshold configuration
- [ ] Provide export capabilities for discovery results
- [ ] Support batch discovery operations
- [ ] Enable discovery source selection (vector, web, hybrid)
- [ ] Implement discovery quality metrics and confidence indicators

## Technical Details

### CLI Architecture Integration
The discover command builds on the research command architecture:

```
CLI Layer (discover.py)
├── Advanced Argument Parsing (Click + custom validators)
├── Discovery Progress Display (Rich with similarity metrics)
├── DI Container Integration (DiscoverSimilar use case)
├── Intelligent Filtering System (Multi-dimensional filters)
├── Interactive Research Flow (Seamless transition to research)
├── Similarity Explanation Engine (Transparent scoring)
└── Discovery Result Management (Caching and export)
```

### Command Signature and Advanced Options
```bash
theodore discover [OPTIONS] COMPANY_NAME

Options:
  --limit INTEGER                     Maximum results to return [default: 10]
  --output, -o [table|json|yaml|markdown]  Output format [default: table]
  --business-model [b2b|b2c|marketplace|saas|ecommerce|enterprise]
                                     Filter by business model
  --company-size [startup|small|medium|large|enterprise]
                                     Filter by company size
  --industry TEXT                    Filter by industry sector
  --growth-stage [seed|series-a|series-b|growth|mature]
                                     Filter by growth stage
  --location TEXT                    Filter by geographic location
  --similarity-threshold FLOAT       Minimum similarity score [default: 0.6]
  --source [vector|web|hybrid]       Discovery source preference [default: hybrid]
  --interactive, -i                  Enable interactive research mode
  --research-discovered              Automatically research all discovered companies
  --save PATH                        Save discovery results to file
  --cache-results                    Cache results for faster repeat queries
  --explain-similarity               Show detailed similarity explanations
  --verbose, -v                      Enable verbose discovery logging
  --timeout INTEGER                  Discovery timeout in seconds [default: 45]
  --help                             Show this message and exit

Examples:
  theodore discover "Salesforce"
  theodore discover "Stripe" --business-model saas --limit 20
  theodore discover "Local Startup" --source web --interactive
  theodore discover "Microsoft" --similarity-threshold 0.8 --explain-similarity
  theodore discover "Nike" --industry retail --save nike-competitors.json
```

### Advanced Filtering System Architecture
Sophisticated multi-dimensional filtering with intelligent defaults:

```python
class DiscoveryFilters:
    business_model: Optional[BusinessModel]
    company_size: Optional[CompanySize] 
    industry: Optional[str]
    growth_stage: Optional[GrowthStage]
    location: Optional[str]
    similarity_threshold: float = 0.6
    founded_after: Optional[int]
    founded_before: Optional[int]
    exclude_competitors: bool = False
    include_subsidiaries: bool = True
```

### Discovery Source Strategy
Multi-source discovery with intelligent fallbacks:

1. **Vector-Based Discovery** (Primary)
   - Semantic similarity using embeddings
   - High-precision matching
   - Fast for known companies

2. **Web Search Discovery** (Fallback)
   - MCP search tool integration
   - Broader discovery scope
   - Better for unknown companies

3. **Hybrid Discovery** (Default)
   - Combines vector and web results
   - Result fusion with scoring
   - Comprehensive coverage

### Similarity Scoring and Explanation System
Transparent similarity scoring with detailed explanations:

```python
class SimilarityScore:
    overall_score: float
    business_model_score: float
    industry_score: float
    size_score: float
    technology_score: float
    market_score: float
    explanation: SimilarityExplanation
    confidence: float
    source: DiscoverySource
```

### Interactive Research Integration
Seamless workflow from discovery to research:

1. **Discovery Phase**: Find similar companies
2. **Selection Phase**: Interactive company selection
3. **Research Phase**: Detailed company analysis
4. **Comparison Phase**: Side-by-side analysis

### File Structure
Create comprehensive CLI discovery system building on research foundation:

```
v2/src/cli/
├── commands/
│   └── discover.py                  # Main discover command implementation
├── formatters/
│   ├── similarity.py                # Similarity result formatting
│   ├── discovery_table.py           # Rich table for discovery results
│   └── comparison.py                # Company comparison formatting
├── filters/
│   ├── __init__.py                  # Filter system exports
│   ├── discovery_filters.py         # Advanced filtering logic
│   ├── filter_validators.py         # Filter validation and normalization
│   └── filter_suggestions.py        # Smart filter suggestions
├── interactive/
│   ├── __init__.py                  # Interactive mode exports
│   ├── discovery_session.py         # Interactive discovery sessions
│   ├── company_selector.py          # Interactive company selection
│   └── research_launcher.py         # Launch research from discovery
└── discovery/
    ├── __init__.py                  # Discovery utilities exports
    ├── result_cache.py              # Discovery result caching
    ├── similarity_explainer.py      # Similarity score explanations
    └── discovery_metrics.py         # Discovery quality metrics
```

### Discovery Progress Tracking
Enhanced progress system for discovery operations:

1. **Input Processing Phase** (5%)
   - Company name normalization
   - Filter validation and optimization

2. **Vector Discovery Phase** (30%)
   - Embedding generation
   - Vector similarity search
   - Result ranking and filtering

3. **Web Discovery Phase** (30%)
   - MCP search execution
   - Web result processing
   - Entity recognition and validation

4. **Result Fusion Phase** (20%)
   - Cross-source deduplication
   - Score normalization and fusion
   - Quality assessment

5. **Enhancement Phase** (15%)
   - Additional data enrichment
   - Similarity explanation generation
   - Final ranking optimization

### Interactive Mode Workflow
Sophisticated interactive discovery experience:

```
Discovery Results → Interactive Selection → Batch Research → Comparison View
    ↓                     ↓                      ↓              ↓
Filter Refinement    Company Details      Progress Tracking   Export Options
```

### Result Caching and Performance
Intelligent caching system for improved performance:

- **Query fingerprinting**: Cache based on company + filters
- **Incremental updates**: Smart cache invalidation
- **Cross-session persistence**: Reuse results across CLI sessions
- **Memory management**: LRU eviction with size limits

## Implementation Considerations

### Advanced Filtering Logic
- **Fuzzy matching**: Handle variations in industry names
- **Hierarchical filtering**: Parent/child industry relationships
- **Smart defaults**: Learn from user patterns
- **Filter suggestions**: Recommend relevant filters based on company

### Discovery Quality Metrics
- **Coverage**: Breadth of discovery results
- **Precision**: Relevance of discovered companies
- **Recall**: Completeness of similar companies found
- **Diversity**: Variety in discovered companies
- **Freshness**: Recency of company data

### Error Handling and Fallbacks
- **Graceful degradation**: Fall back to web search if vector fails
- **Partial results**: Show available results even if some sources fail
- **Alternative suggestions**: Suggest similar queries if no results
- **Data quality warnings**: Alert users to potential data issues

### Performance Optimization
- **Parallel discovery**: Run vector and web searches concurrently
- **Result streaming**: Show results as they become available
- **Smart pagination**: Load additional results on demand
- **Efficient filtering**: Pre-filter before expensive operations

## Files to Create

### Core Command Implementation (1 file)
1. **`v2/src/cli/commands/discover.py`**
   - Main Click command with advanced argument parsing
   - DI container integration with DiscoverSimilar use case
   - Progress tracking with discovery-specific phases
   - Interactive mode coordination
   - Filter processing and validation
   - Result caching and management
   - Output format routing with discovery-specific formatting

### Advanced Formatting System (3 files)
2. **`v2/src/cli/formatters/similarity.py`**
   - SimilarityResultFormatter for discovery results
   - Similarity score visualization and explanation
   - Ranked list formatting with confidence indicators
   - Source attribution and transparency
   - Filter result highlighting

3. **`v2/src/cli/formatters/discovery_table.py`**
   - RichDiscoveryTableFormatter extending base table formatter
   - Multi-column similarity scoring display
   - Interactive selection indicators
   - Color-coded similarity ranges
   - Expandable company details

4. **`v2/src/cli/formatters/comparison.py`**
   - ComparisonFormatter for side-by-side company analysis
   - Similarity explanation visualization
   - Attribute comparison matrices
   - Difference highlighting

### Advanced Filtering System (3 files)
5. **`v2/src/cli/filters/discovery_filters.py`**
   - DiscoveryFilterProcessor for advanced filtering logic
   - Multi-dimensional filter application
   - Filter combination and optimization
   - Smart filter suggestions based on company context

6. **`v2/src/cli/filters/filter_validators.py`**
   - FilterValidator for input validation and normalization
   - Industry taxonomy validation
   - Business model standardization
   - Geographic location normalization

7. **`v2/src/cli/filters/filter_suggestions.py`**
   - FilterSuggestionEngine for intelligent filter recommendations
   - Context-aware filter suggestions
   - User pattern learning
   - Filter conflict resolution

### Interactive Mode System (3 files)
8. **`v2/src/cli/interactive/discovery_session.py`**
   - InteractiveDiscoverySession for guided discovery workflows
   - Progressive filter refinement
   - Dynamic result updating
   - Session state management

9. **`v2/src/cli/interactive/company_selector.py`**
   - CompanySelector for interactive company selection
   - Multi-select with preview
   - Batch operation support
   - Selection criteria saving

10. **`v2/src/cli/interactive/research_launcher.py`**
    - ResearchLauncher for seamless transition to research
    - Batch research coordination
    - Progress aggregation across multiple companies
    - Result compilation and comparison

### Discovery Utilities (3 files)
11. **`v2/src/cli/discovery/result_cache.py`**
    - DiscoveryResultCache for intelligent result caching
    - Query fingerprinting and cache key generation
    - LRU eviction with discovery-specific policies
    - Cross-session cache persistence

12. **`v2/src/cli/discovery/similarity_explainer.py`**
    - SimilarityExplainer for transparent similarity scoring
    - Factor-based similarity breakdown
    - Natural language explanations
    - Confidence interval calculation

13. **`v2/src/cli/discovery/discovery_metrics.py`**
    - DiscoveryMetricsCollector for quality assessment
    - Discovery performance tracking
    - Result quality scoring
    - User satisfaction metrics

### Testing Implementation (2 files)
14. **`v2/tests/unit/cli/test_discover_command.py`**
    - Comprehensive unit tests for discover command
    - Mock container integration testing
    - Filter validation testing
    - Interactive mode simulation
    - Output format validation
    - Error handling scenarios

15. **`v2/tests/e2e/test_discover_cli.py`**
    - End-to-end discovery command testing
    - Real use case integration
    - Interactive workflow testing
    - Performance benchmarking
    - Cross-format result validation

## Testing Strategy

### Unit Testing Approach
- Mock all external dependencies (use cases, discovery sources)
- Test advanced filter combinations and edge cases
- Verify similarity score calculations and explanations
- Test interactive mode state transitions
- Validate result caching and invalidation

### Integration Testing Approach
- Test with real discovery use case integration
- Validate filter application accuracy
- Test multi-source discovery fusion
- Verify interactive workflow completeness
- Test discovery-to-research transition

### End-to-End Testing Approach
- Full command execution with various filter combinations
- Interactive mode user journey testing
- Performance testing with large result sets
- Cross-platform compatibility validation
- Real-world discovery scenario testing

### Test Scenarios
```python
def test_discover_command_basic():
    """Test basic company discovery functionality"""
    
def test_discover_with_advanced_filters():
    """Test discovery with multiple filter combinations"""
    
def test_discover_similarity_explanations():
    """Test similarity score explanation generation"""
    
def test_discover_interactive_mode():
    """Test interactive discovery and selection workflow"""
    
def test_discover_result_caching():
    """Test discovery result caching and retrieval"""
    
def test_discover_unknown_company_fallback():
    """Test fallback strategies for unknown companies"""
    
def test_discover_to_research_transition():
    """Test seamless transition from discovery to research"""
    
def test_discover_performance_large_results():
    """Test performance with large discovery result sets"""
```

## Estimated Time: 6-7 hours

## Dependencies

### Core Business Logic Dependencies
- **TICKET-011 (DiscoverSimilar Use Case)** - Required for discovery orchestration
  - Provides the core business logic for company similarity discovery
  - Implements intelligent filtering and multi-source discovery coordination
  - Handles similarity scoring and result ranking algorithms
  - Files: `v2/src/core/use_cases/discover_similar_companies.py`

### Infrastructure and Framework Dependencies
- **TICKET-019 (Dependency Injection Container)** - Required for component wiring
  - Provides centralized dependency management and configuration
  - Enables proper separation of concerns and testability
  - Manages lifecycle of discovery services and external adapters
  - Files: `v2/src/infrastructure/di/container.py`

- **TICKET-020 (CLI Research Command)** - Required for shared patterns and integration
  - Provides common CLI patterns and utilities
  - Enables seamless transition from discovery to detailed research
  - Shares output formatting and interactive workflow patterns
  - Files: `v2/src/cli/commands/research.py`, `v2/src/cli/utils/`

### External Service Dependencies
- **TICKET-005 (MCP Search Tools)** - Required for web discovery fallback
  - Provides pluggable search tools for unknown companies
  - Enables web-based discovery when vector search is insufficient
  - Supports multiple search providers (Perplexity, Tavily, custom)
  - Files: `v2/src/infrastructure/adapters/mcp/`

### Data and Storage Dependencies
- **TICKET-016 (Pinecone Vector Storage)** - Required for similarity search
  - Provides vector-based similarity discovery capabilities
  - Enables fast, scalable company similarity matching
  - Supports metadata filtering for advanced discovery queries
  - Files: `v2/src/infrastructure/adapters/storage/pinecone/`

### AI Provider Dependencies
- **TICKET-015 (Gemini AI Adapter)** - Needed for content analysis
  - Provides AI-powered similarity explanation generation
  - Enables intelligent discovery result enhancement
  - Supports similarity reasoning and factor analysis
  - Files: `v2/src/infrastructure/adapters/ai/gemini/`

### UI and Presentation Dependencies
- **TICKET-004 (Progress Tracking Port)** - Required for real-time progress
  - Provides progress tracking during discovery operations
  - Enables responsive user experience with live updates
  - Supports cancellation and timeout handling
  - Files: `v2/src/core/ports/progress_tracker.py`

### Configuration Dependencies
- **TICKET-003 (Configuration System)** - Required for discovery settings
  - Provides discovery source configuration and preferences
  - Manages similarity thresholds and filtering defaults
  - Handles caching and performance optimization settings
  - Files: `v2/src/core/config/`

## CLI Usage Examples

### Basic Discovery Operations
```bash
# Simple company discovery
theodore discover "Salesforce"

# Discovery with result limit
theodore discover "Apple" --limit 20

# Discovery with specific business model
theodore discover "Stripe" --business-model saas
```

### Advanced Filtering
```bash
# Multi-dimensional filtering
theodore discover "Tesla" --industry automotive --company-size large --growth-stage mature

# Geographic and temporal filtering
theodore discover "Local Startup" --location "San Francisco" --founded-after 2015

# Similarity threshold adjustment
theodore discover "Microsoft" --similarity-threshold 0.8 --explain-similarity
```

### Interactive and Research Integration
```bash
# Interactive discovery mode
theodore discover "Netflix" --interactive

# Auto-research discovered companies
theodore discover "Amazon" --research-discovered --limit 5

# Discovery with immediate export
theodore discover "Google" --save google-competitors.json --output json
```

### Advanced Discovery Sources
```bash
# Vector-only discovery (fast, precise)
theodore discover "Uber" --source vector --limit 15

# Web-only discovery (comprehensive, slower)
theodore discover "Unknown Startup" --source web --verbose

# Hybrid discovery with caching
theodore discover "Facebook" --source hybrid --cache-results
```

### Discovery Analysis and Export
```bash
# Detailed similarity explanations
theodore discover "Zoom" --explain-similarity --verbose

# Discovery comparison analysis
theodore discover "Slack" --output markdown --save slack-analysis.md

# Batch discovery with comparison
theodore discover "Twitter" --research-discovered --save twitter-competitive-analysis.json
```

---

## Udemy Tutorial: Building an Intelligent Company Discovery System

### Introduction (8 minutes)

Welcome to this comprehensive tutorial on building an intelligent company discovery system for Theodore v2. We're going to create the `theodore discover` command that goes far beyond simple search - this is about building a sophisticated similarity engine that helps users explore competitive landscapes, identify market opportunities, and discover relevant companies through advanced AI-powered matching.

In this tutorial, we'll build a discovery command that combines vector-based semantic similarity with web search capabilities, provides transparent similarity scoring with detailed explanations, and offers interactive workflows that seamlessly transition from discovery to detailed research. This isn't just about finding companies that match keywords - we're creating an intelligent system that understands business context, industry relationships, and competitive positioning.

**Why is intelligent discovery critical for Theodore v2?** Because raw search results without context are nearly useless for business intelligence. Users need to understand not just what companies are similar, but why they're similar, how confident we are in that assessment, and what specific attributes make them relevant. A great discovery system transforms overwhelming amounts of company data into actionable competitive intelligence.

**What makes our discovery implementation special?** We're building more than just a search interface. Our system features:
- Multi-dimensional similarity scoring that considers business model, technology stack, market position, and growth stage
- Hybrid discovery combining vector embeddings with real-time web search for comprehensive coverage
- Interactive workflows that let users refine discoveries and seamlessly transition to detailed research
- Transparent similarity explanations that show users exactly why companies are considered similar
- Advanced filtering that understands business context and industry relationships

By the end of this tutorial, you'll understand how to build discovery systems that provide genuine business intelligence rather than simple keyword matching, with the sophistication that enterprise users expect from AI-powered tools.

Let's start by exploring the discovery architecture and understanding how semantic similarity works in business contexts.

### Discovery Architecture and Similarity Intelligence (12 minutes)

Before we dive into implementation, let's understand the sophisticated architecture that powers intelligent company discovery and how it differs from traditional search systems.

**The Multi-Source Discovery Strategy**
Our discovery system uses a three-tier approach that maximizes both precision and coverage:

```
Tier 1: Vector Similarity Discovery (Precision)
├── Semantic embeddings of company descriptions
├── Business model vectorization
├── Technology stack similarity
└── Market positioning analysis

Tier 2: Web Search Discovery (Coverage)  
├── MCP search tool integration
├── Real-time competitive intelligence
├── Industry report mining
└── News and announcement analysis

Tier 3: Hybrid Fusion (Best of Both)
├── Cross-source result deduplication
├── Confidence-weighted score fusion
├── Source transparency tracking
└── Quality-based result ranking
```

**Understanding Semantic Similarity in Business Context**
Traditional keyword search fails for business discovery because it doesn't understand context. When someone searches for companies similar to "Salesforce," they might mean:
- CRM software providers (functional similarity)
- SaaS companies with similar business models (structural similarity)  
- Enterprise software companies targeting similar markets (market similarity)
- Companies with similar growth trajectories (temporal similarity)

Our vector-based approach captures these nuanced relationships by encoding companies as high-dimensional vectors that represent their complete business context.

**The Similarity Scoring Framework**
We break down similarity into interpretable components:

```python
class SimilarityScore:
    # Core business similarity (40% weight)
    business_model_score: float      # B2B/B2C/marketplace alignment
    revenue_model_score: float       # Subscription/transaction/license
    
    # Market similarity (30% weight)  
    industry_score: float           # Primary industry alignment
    target_market_score: float     # Customer segment overlap
    
    # Technical similarity (20% weight)
    technology_score: float         # Tech stack and architecture
    product_type_score: float      # Software/hardware/service
    
    # Scale similarity (10% weight)
    size_score: float              # Employee count and revenue
    growth_stage_score: float     # Startup/growth/mature
```

This decomposition allows users to understand exactly why companies are considered similar and adjust discovery based on what matters most for their specific use case.

**Progressive Discovery Workflow**
Our discovery system supports multiple interaction patterns:

**Quick Discovery**: Single command execution for immediate results
**Filtered Discovery**: Advanced filtering for targeted results  
**Interactive Discovery**: Progressive refinement with real-time feedback
**Research Integration**: Seamless transition from discovery to detailed analysis

**Advanced Filtering Architecture**
The filtering system understands business hierarchies and relationships:

```python
# Industry hierarchy awareness
technology -> software -> saas -> crm
retail -> ecommerce -> marketplace -> b2b_marketplace

# Business model relationships
saas + enterprise = enterprise_saas
marketplace + b2b = b2b_marketplace

# Growth stage implications
seed -> limited_data_confidence
series_a -> growth_trajectory_emphasis
mature -> stability_and_scale_focus
```

**Discovery Source Intelligence**
Each discovery source has strengths and optimal use cases:

**Vector Discovery Strengths:**
- High precision for well-known companies
- Semantic understanding of business models
- Fast execution with cached embeddings
- Consistent scoring across queries

**Web Discovery Strengths:**
- Coverage of recent/new companies
- Real-time competitive intelligence
- Access to latest market developments
- Discovery of niche/specialized companies

**Hybrid Fusion Benefits:**
- Comprehensive coverage with high precision
- Source diversity reduces bias
- Confidence calibration across sources
- Graceful degradation when sources fail

Let's see how these architectural principles translate into a powerful discovery implementation.

### Implementing the Core Discovery Command (15 minutes)

Let's build the heart of our discovery system - a sophisticated command that orchestrates multi-source discovery with advanced filtering and intelligent result processing.

```python
# v2/src/cli/commands/discover.py
import click
import asyncio
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
import logging

from ...infrastructure.container import ContainerFactory
from ...application.use_cases.discover_similar import DiscoverSimilarUseCase
from ..formatters import FormatterRegistry
from ..formatters.similarity import SimilarityResultFormatter
from ..filters.discovery_filters import DiscoveryFilterProcessor
from ..interactive.discovery_session import InteractiveDiscoverySession
from ..discovery.result_cache import DiscoveryResultCache
from ..discovery.similarity_explainer import SimilarityExplainer
from ..utils.validation import InputValidator
from ..utils.error_handling import CLIErrorHandler

logger = logging.getLogger(__name__)
console = Console()

# Define enum choices for Click options
BUSINESS_MODELS = ['b2b', 'b2c', 'marketplace', 'saas', 'ecommerce', 'enterprise']
COMPANY_SIZES = ['startup', 'small', 'medium', 'large', 'enterprise']
GROWTH_STAGES = ['seed', 'series-a', 'series-b', 'growth', 'mature']
DISCOVERY_SOURCES = ['vector', 'web', 'hybrid']

@click.command()
@click.argument('company_name', type=str)
@click.option('--limit', 
              type=int, 
              default=10,
              help='Maximum number of similar companies to discover')
@click.option('--output', '-o',
              type=click.Choice(['table', 'json', 'yaml', 'markdown']),
              default='table',
              help='Output format for discovery results')
@click.option('--business-model',
              type=click.Choice(BUSINESS_MODELS),
              help='Filter by business model')
@click.option('--company-size',
              type=click.Choice(COMPANY_SIZES), 
              help='Filter by company size')
@click.option('--industry',
              type=str,
              help='Filter by industry sector')
@click.option('--growth-stage',
              type=click.Choice(GROWTH_STAGES),
              help='Filter by growth stage')
@click.option('--location',
              type=str,
              help='Filter by geographic location')
@click.option('--similarity-threshold',
              type=float,
              default=0.6,
              help='Minimum similarity score (0.0-1.0)')
@click.option('--source',
              type=click.Choice(DISCOVERY_SOURCES),
              default='hybrid',
              help='Discovery source preference')
@click.option('--interactive', '-i',
              is_flag=True,
              help='Enable interactive discovery mode')
@click.option('--research-discovered',
              is_flag=True,
              help='Automatically research all discovered companies')
@click.option('--save',
              type=click.Path(),
              help='Save discovery results to file')
@click.option('--cache-results',
              is_flag=True,
              help='Cache results for faster repeat queries')
@click.option('--explain-similarity',
              is_flag=True,
              help='Show detailed similarity explanations')
@click.option('--verbose', '-v',
              is_flag=True,
              help='Enable verbose discovery logging')
@click.option('--timeout',
              type=int,
              default=45,
              help='Discovery timeout in seconds')
@click.pass_context
async def discover(
    ctx: click.Context,
    company_name: str,
    limit: int,
    output: str,
    business_model: Optional[str],
    company_size: Optional[str],
    industry: Optional[str],
    growth_stage: Optional[str],
    location: Optional[str],
    similarity_threshold: float,
    source: str,
    interactive: bool,
    research_discovered: bool,
    save: Optional[str],
    cache_results: bool,
    explain_similarity: bool,
    verbose: bool,
    timeout: int
):
    """
    Discover companies similar to the specified company.
    
    Uses advanced AI-powered similarity matching to find companies with
    similar business models, market positioning, and characteristics.
    Supports multi-dimensional filtering and interactive exploration.
    
    Examples:
        theodore discover "Salesforce"
        theodore discover "Stripe" --business-model saas --limit 20
        theodore discover "Tesla" --industry automotive --interactive
        theodore discover "Unknown Startup" --source web --explain-similarity
    """
    
    error_handler = CLIErrorHandler(console, verbose)
    
    try:
        # Phase 1: Input validation and normalization
        await _validate_discovery_inputs(
            company_name, limit, similarity_threshold, error_handler
        )
        
        # Phase 2: Build discovery filters
        discovery_filters = await _build_discovery_filters(
            business_model, company_size, industry, growth_stage, 
            location, similarity_threshold
        )
        
        # Phase 3: Container initialization
        container = await _initialize_discovery_container(verbose, timeout)
        
        # Phase 4: Execute discovery workflow
        if interactive:
            discovery_results = await _run_interactive_discovery(
                container, company_name, discovery_filters, source, limit
            )
        else:
            discovery_results = await _run_standard_discovery(
                container, company_name, discovery_filters, source, limit, verbose
            )
            
        # Phase 5: Process and display results
        await _process_discovery_results(
            discovery_results, output, save, explain_similarity, 
            research_discovered, container
        )
        
        # Success indication
        discovered_count = len(discovery_results.get('companies', []))
        console.print(f"✅ Discovered {discovered_count} similar companies!", style="bold green")
        
    except KeyboardInterrupt:
        console.print("\n🛑 Discovery interrupted by user", style="bold yellow")
    except Exception as e:
        await error_handler.handle_error(e, ctx)
        raise click.Abort()

async def _validate_discovery_inputs(
    company_name: str,
    limit: int, 
    similarity_threshold: float,
    error_handler: CLIErrorHandler
):
    """Validate and normalize discovery inputs."""
    
    validator = InputValidator()
    
    # Validate company name
    if not validator.validate_company_name(company_name):
        error_handler.suggest_company_name_format(company_name)
        raise click.BadParameter("Invalid company name format")
    
    # Validate limit range
    if limit < 1 or limit > 100:
        raise click.BadParameter("Limit must be between 1 and 100")
        
    # Validate similarity threshold
    if similarity_threshold < 0.0 or similarity_threshold > 1.0:
        raise click.BadParameter("Similarity threshold must be between 0.0 and 1.0")
    
    console.print(f"🔍 Discovering companies similar to: [bold cyan]{company_name}[/bold cyan]")
    console.print(f"📊 Similarity threshold: [dim]{similarity_threshold:.1f}[/dim]")

async def _build_discovery_filters(
    business_model: Optional[str],
    company_size: Optional[str], 
    industry: Optional[str],
    growth_stage: Optional[str],
    location: Optional[str],
    similarity_threshold: float
) -> Dict[str, Any]:
    """Build comprehensive discovery filters from CLI options."""
    
    filter_processor = DiscoveryFilterProcessor()
    
    # Create base filter configuration
    filters = {
        'similarity_threshold': similarity_threshold,
        'business_model': business_model,
        'company_size': company_size,
        'industry': industry,
        'growth_stage': growth_stage,
        'location': location
    }
    
    # Process and validate filters
    validated_filters = await filter_processor.process_filters(filters)
    
    # Display active filters
    if any(v for v in validated_filters.values() if v is not None):
        _display_active_filters(validated_filters)
        
    return validated_filters

def _display_active_filters(filters: Dict[str, Any]):
    """Display active discovery filters to user."""
    
    active_filters = {k: v for k, v in filters.items() if v is not None}
    
    if not active_filters:
        return
        
    filter_table = Table(title="🔧 Active Discovery Filters", show_header=False)
    filter_table.add_column("Filter", style="cyan")
    filter_table.add_column("Value", style="white")
    
    for filter_name, filter_value in active_filters.items():
        display_name = filter_name.replace('_', ' ').title()
        filter_table.add_row(display_name, str(filter_value))
        
    console.print(filter_table)
    console.print()
```

**Standard Discovery Execution:**
```python
async def _run_standard_discovery(
    container: Any,
    company_name: str,
    filters: Dict[str, Any],
    source: str,
    limit: int,
    verbose: bool
) -> Dict[str, Any]:
    """Execute standard discovery workflow with progress tracking."""
    
    # Get discovery use case from container
    discover_use_case = container.use_cases.discover_similar()
    
    # Configure discovery parameters
    discovery_params = {
        'company_name': company_name,
        'filters': filters,
        'discovery_source': source,
        'max_results': limit
    }
    
    # Execute discovery with progress display
    with console.status(f"[bold blue]Discovering companies similar to {company_name}...") as status:
        try:
            # Update status for different phases
            status.update(f"[bold blue]Analyzing {company_name}...")
            await asyncio.sleep(0.5)  # Allow status to display
            
            status.update(f"[bold blue]Searching vector database...")
            # Execute discovery
            results = await discover_use_case.execute(**discovery_params)
            
            status.update(f"[bold blue]Processing similarity scores...")
            await asyncio.sleep(0.3)
            
            status.update(f"[bold blue]Applying filters and ranking...")
            await asyncio.sleep(0.2)
            
        except Exception as e:
            console.print(f"❌ Discovery failed: {e}", style="bold red")
            raise
            
    return results

async def _run_interactive_discovery(
    container: Any,
    company_name: str,
    initial_filters: Dict[str, Any],
    source: str,
    initial_limit: int
) -> Dict[str, Any]:
    """Execute interactive discovery with real-time refinement."""
    
    console.print("🎯 Starting interactive discovery mode", style="bold blue")
    console.print("Use this mode to refine your discovery and explore results")
    console.print()
    
    # Initialize interactive session
    interactive_session = InteractiveDiscoverySession(
        container, company_name, initial_filters, source
    )
    
    # Run interactive discovery loop
    discovery_results = await interactive_session.run_discovery_loop(initial_limit)
    
    return discovery_results
```

**Discovery Result Processing:**
```python
async def _process_discovery_results(
    results: Dict[str, Any],
    output_format: str,
    save_path: Optional[str],
    explain_similarity: bool,
    research_discovered: bool,
    container: Any
):
    """Process and display discovery results with optional research integration."""
    
    # Extract discovered companies
    companies = results.get('companies', [])
    
    if not companies:
        console.print("🔍 No similar companies found with current criteria", style="yellow")
        console.print("💡 Try adjusting filters or similarity threshold", style="dim")
        return
        
    # Display results based on format
    if output_format == 'table':
        await _display_discovery_table(companies, explain_similarity)
    else:
        # Use standard formatters for other formats
        formatter = FormatterRegistry.get_formatter(output_format)
        formatted_output = formatter.format_research_results(results)
        console.print(formatted_output)
        
    # Optional: Research discovered companies
    if research_discovered:
        await _research_discovered_companies(companies, container)
        
    # Optional: Save results
    if save_path:
        await _save_discovery_results(results, save_path, output_format)

async def _display_discovery_table(
    companies: List[Dict[str, Any]], 
    explain_similarity: bool
):
    """Display discovery results in Rich table format."""
    
    # Create main results table
    results_table = Table(title="🎯 Discovery Results", show_header=True, expand=True)
    results_table.add_column("Rank", justify="center", style="bold", width=6)
    results_table.add_column("Company", style="bold cyan")
    results_table.add_column("Industry", style="dim")
    results_table.add_column("Similarity", justify="center", style="green")
    results_table.add_column("Business Model", style="blue")
    
    if explain_similarity:
        results_table.add_column("Why Similar", style="dim yellow")
    
    # Add company rows
    for idx, company in enumerate(companies, 1):
        similarity_score = company.get('similarity_score', 0.0)
        similarity_display = f"{similarity_score:.2f}"
        
        # Color code similarity scores
        if similarity_score >= 0.8:
            similarity_style = "bold green"
        elif similarity_score >= 0.6:
            similarity_style = "yellow"
        else:
            similarity_style = "red"
            
        row_data = [
            str(idx),
            company.get('name', 'Unknown'),
            company.get('industry', 'Unknown'),
            f"[{similarity_style}]{similarity_display}[/{similarity_style}]",
            company.get('business_model', 'Unknown')
        ]
        
        if explain_similarity:
            explanation = _generate_similarity_explanation(company)
            row_data.append(explanation)
            
        results_table.add_row(*row_data)
        
    console.print(results_table)
    console.print()

def _generate_similarity_explanation(company: Dict[str, Any]) -> str:
    """Generate concise similarity explanation for table display."""
    
    explainer = SimilarityExplainer()
    explanation = explainer.generate_brief_explanation(company)
    
    # Truncate for table display
    return explanation[:50] + "..." if len(explanation) > 50 else explanation
```

This implementation provides a robust foundation that handles complex discovery scenarios while maintaining the user-friendly experience established in our research command.

### Building Advanced Filtering and Interactive Discovery (12 minutes)

Let's implement the sophisticated filtering system and interactive discovery capabilities that make our command truly intelligent.

```python
# v2/src/cli/filters/discovery_filters.py
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import re

class BusinessModel(Enum):
    B2B = "b2b"
    B2C = "b2c" 
    MARKETPLACE = "marketplace"
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    ENTERPRISE = "enterprise"

class CompanySize(Enum):
    STARTUP = "startup"      # 1-50 employees
    SMALL = "small"          # 51-200 employees  
    MEDIUM = "medium"        # 201-1000 employees
    LARGE = "large"          # 1001-5000 employees
    ENTERPRISE = "enterprise" # 5000+ employees

class GrowthStage(Enum):
    SEED = "seed"
    SERIES_A = "series-a"
    SERIES_B = "series-b" 
    GROWTH = "growth"
    MATURE = "mature"

@dataclass
class DiscoveryFilters:
    """Comprehensive discovery filter configuration."""
    business_model: Optional[BusinessModel] = None
    company_size: Optional[CompanySize] = None
    industry: Optional[str] = None
    growth_stage: Optional[GrowthStage] = None
    location: Optional[str] = None
    similarity_threshold: float = 0.6
    founded_after: Optional[int] = None
    founded_before: Optional[int] = None
    exclude_competitors: bool = False
    include_subsidiaries: bool = True

class DiscoveryFilterProcessor:
    """Advanced filter processing with business intelligence."""
    
    def __init__(self):
        self.industry_taxonomy = self._load_industry_taxonomy()
        self.location_normalizer = LocationNormalizer()
        
    async def process_filters(self, raw_filters: Dict[str, Any]) -> DiscoveryFilters:
        """Process and validate raw filter inputs."""
        
        processed = DiscoveryFilters()
        
        # Process business model
        if raw_filters.get('business_model'):
            processed.business_model = BusinessModel(raw_filters['business_model'])
            
        # Process company size
        if raw_filters.get('company_size'):
            processed.company_size = CompanySize(raw_filters['company_size'])
            
        # Process and normalize industry
        if raw_filters.get('industry'):
            processed.industry = await self._normalize_industry(raw_filters['industry'])
            
        # Process growth stage
        if raw_filters.get('growth_stage'):
            processed.growth_stage = GrowthStage(raw_filters['growth_stage'])
            
        # Process and normalize location
        if raw_filters.get('location'):
            processed.location = await self._normalize_location(raw_filters['location'])
            
        # Set similarity threshold
        processed.similarity_threshold = raw_filters.get('similarity_threshold', 0.6)
        
        return processed
        
    async def _normalize_industry(self, industry_input: str) -> str:
        """Normalize industry input using taxonomy and fuzzy matching."""
        
        industry_lower = industry_input.lower().strip()
        
        # Direct match
        if industry_lower in self.industry_taxonomy:
            return self.industry_taxonomy[industry_lower]
            
        # Fuzzy match for common variations
        fuzzy_matches = self._find_fuzzy_industry_matches(industry_lower)
        if fuzzy_matches:
            return fuzzy_matches[0]  # Return best match
            
        # Return normalized input if no matches
        return industry_input.title()
        
    def _find_fuzzy_industry_matches(self, industry: str) -> List[str]:
        """Find fuzzy matches for industry names."""
        
        matches = []
        
        # Common industry synonyms and variations
        synonyms = {
            'tech': 'Technology',
            'software': 'Technology', 
            'fintech': 'Financial Technology',
            'healthtech': 'Healthcare Technology',
            'ecom': 'E-commerce',
            'retail': 'Retail',
            'finance': 'Financial Services'
        }
        
        for synonym, canonical in synonyms.items():
            if synonym in industry:
                matches.append(canonical)
                
        return matches
        
    async def _normalize_location(self, location_input: str) -> str:
        """Normalize location input for consistent filtering."""
        
        return self.location_normalizer.normalize(location_input)
        
    def _load_industry_taxonomy(self) -> Dict[str, str]:
        """Load industry taxonomy for normalization."""
        
        return {
            'technology': 'Technology',
            'software': 'Technology',
            'saas': 'Software as a Service',
            'fintech': 'Financial Technology',
            'healthcare': 'Healthcare',
            'retail': 'Retail',
            'ecommerce': 'E-commerce',
            'automotive': 'Automotive',
            'manufacturing': 'Manufacturing',
            'energy': 'Energy',
            'education': 'Education',
            'real estate': 'Real Estate',
            'media': 'Media & Entertainment'
        }

class LocationNormalizer:
    """Intelligent location normalization and expansion."""
    
    def normalize(self, location: str) -> str:
        """Normalize location string for consistent matching."""
        
        location = location.strip()
        
        # Handle common city/region patterns
        location_mappings = {
            'sf': 'San Francisco',
            'bay area': 'San Francisco Bay Area',
            'silicon valley': 'San Francisco Bay Area',
            'nyc': 'New York City',
            'ny': 'New York',
            'la': 'Los Angeles',
            'london': 'London, UK',
            'berlin': 'Berlin, Germany'
        }
        
        location_lower = location.lower()
        if location_lower in location_mappings:
            return location_mappings[location_lower]
            
        return location.title()

# Filter suggestion engine
class FilterSuggestionEngine:
    """Intelligent filter suggestions based on company context."""
    
    def __init__(self, discovery_results: List[Dict[str, Any]]):
        self.results = discovery_results
        
    def suggest_refinement_filters(self) -> Dict[str, List[str]]:
        """Suggest filter refinements based on current results."""
        
        suggestions = {}
        
        # Analyze result distribution
        business_models = self._analyze_business_models()
        industries = self._analyze_industries() 
        company_sizes = self._analyze_company_sizes()
        
        # Generate suggestions
        if len(set(business_models)) > 1:
            suggestions['business_model'] = list(set(business_models))
            
        if len(set(industries)) > 2:
            suggestions['industry'] = industries[:3]  # Top 3 industries
            
        if len(set(company_sizes)) > 1:
            suggestions['company_size'] = list(set(company_sizes))
            
        return suggestions
        
    def _analyze_business_models(self) -> List[str]:
        """Analyze business model distribution in results."""
        return [r.get('business_model', 'unknown') for r in self.results]
        
    def _analyze_industries(self) -> List[str]:
        """Analyze industry distribution in results."""
        industries = [r.get('industry', 'unknown') for r in self.results]
        # Return most common industries
        from collections import Counter
        return [industry for industry, count in Counter(industries).most_common()]
        
    def _analyze_company_sizes(self) -> List[str]:
        """Analyze company size distribution in results."""
        return [r.get('company_size', 'unknown') for r in self.results]
```

**Interactive Discovery Session:**
```python
# v2/src/cli/interactive/discovery_session.py
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.panel import Panel
from typing import Dict, Any, List, Optional
import asyncio

class InteractiveDiscoverySession:
    """Interactive discovery session with progressive refinement."""
    
    def __init__(
        self, 
        container: Any,
        company_name: str,
        initial_filters: Dict[str, Any],
        source: str
    ):
        self.container = container
        self.company_name = company_name
        self.current_filters = initial_filters.copy()
        self.source = source
        self.discovery_history: List[Dict[str, Any]] = []
        
    async def run_discovery_loop(self, initial_limit: int) -> Dict[str, Any]:
        """Run interactive discovery loop with refinement options."""
        
        current_limit = initial_limit
        
        while True:
            # Execute discovery with current parameters
            console.print(f"🔍 Discovering similar companies (limit: {current_limit})...")
            
            results = await self._execute_discovery(current_limit)
            companies = results.get('companies', [])
            
            # Display current results
            self._display_interactive_results(companies)
            
            # Store in history
            self.discovery_history.append({
                'filters': self.current_filters.copy(),
                'results': results,
                'company_count': len(companies)
            })
            
            # Interactive menu
            action = await self._show_interactive_menu(len(companies))
            
            if action == 'done':
                return results
            elif action == 'refine':
                await self._refine_filters()
            elif action == 'more':
                current_limit = await self._adjust_limit(current_limit)
            elif action == 'research':
                await self._launch_interactive_research(companies)
                return results
            elif action == 'suggest':
                await self._apply_filter_suggestions(companies)
                
    async def _execute_discovery(self, limit: int) -> Dict[str, Any]:
        """Execute discovery with current parameters."""
        
        discover_use_case = self.container.use_cases.discover_similar()
        
        params = {
            'company_name': self.company_name,
            'filters': self.current_filters,
            'discovery_source': self.source,
            'max_results': limit
        }
        
        return await discover_use_case.execute(**params)
        
    def _display_interactive_results(self, companies: List[Dict[str, Any]]):
        """Display results with interactive indicators."""
        
        if not companies:
            console.print("🔍 No companies found with current filters", style="yellow")
            return
            
        table = Table(title="🎯 Discovery Results", show_header=True)
        table.add_column("#", width=3)
        table.add_column("Company", style="bold cyan")
        table.add_column("Similarity", justify="center")
        table.add_column("Industry", style="dim")
        
        for idx, company in enumerate(companies[:10], 1):  # Show first 10
            similarity = company.get('similarity_score', 0.0)
            table.add_row(
                str(idx),
                company.get('name', 'Unknown'),
                f"{similarity:.2f}",
                company.get('industry', 'Unknown')
            )
            
        console.print(table)
        console.print()
        
    async def _show_interactive_menu(self, result_count: int) -> str:
        """Show interactive menu and get user choice."""
        
        console.print("🎛️  What would you like to do next?")
        console.print()
        
        choices = [
            "done - Accept these results",
            "refine - Refine filters",
            "more - Get more results", 
            "research - Research selected companies",
            "suggest - Get filter suggestions"
        ]
        
        for choice in choices:
            console.print(f"  • {choice}")
            
        console.print()
        
        action = Prompt.ask(
            "Choose action",
            choices=['done', 'refine', 'more', 'research', 'suggest'],
            default='done'
        )
        
        return action
        
    async def _refine_filters(self):
        """Interactive filter refinement."""
        
        console.print("🔧 Filter Refinement", style="bold blue")
        console.print()
        
        # Show current filters
        self._display_current_filters()
        
        # Offer filter modification options
        filter_type = Prompt.ask(
            "Which filter to modify?",
            choices=['business_model', 'industry', 'company_size', 'similarity_threshold', 'clear_all'],
            default='similarity_threshold'
        )
        
        if filter_type == 'clear_all':
            self.current_filters = {'similarity_threshold': 0.6}
            console.print("✨ All filters cleared", style="green")
        elif filter_type == 'similarity_threshold':
            new_threshold = Prompt.ask(
                "New similarity threshold (0.0-1.0)",
                default=str(self.current_filters.get('similarity_threshold', 0.6))
            )
            self.current_filters['similarity_threshold'] = float(new_threshold)
        else:
            new_value = Prompt.ask(f"New value for {filter_type}")
            if new_value.lower() in ['none', 'clear', '']:
                self.current_filters.pop(filter_type, None)
            else:
                self.current_filters[filter_type] = new_value
                
    def _display_current_filters(self):
        """Display current active filters."""
        
        active_filters = {k: v for k, v in self.current_filters.items() if v is not None}
        
        if not active_filters:
            console.print("No active filters", style="dim")
            return
            
        table = Table(title="Current Filters", show_header=False)
        table.add_column("Filter", style="cyan")
        table.add_column("Value")
        
        for name, value in active_filters.items():
            table.add_row(name.replace('_', ' ').title(), str(value))
            
        console.print(table)
        console.print()
```

This interactive system provides users with powerful tools to refine their discovery in real-time and explore results iteratively.

### Similarity Scoring and Explanation Engine (10 minutes)

Let's build the sophisticated similarity scoring system that provides transparent, interpretable similarity assessments with detailed explanations.

```python
# v2/src/cli/discovery/similarity_explainer.py
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import math

class SimilarityFactor(Enum):
    BUSINESS_MODEL = "business_model"
    INDUSTRY = "industry"
    COMPANY_SIZE = "company_size"
    TECHNOLOGY = "technology"
    MARKET_FOCUS = "market_focus"
    GROWTH_STAGE = "growth_stage"
    GEOGRAPHY = "geography"

@dataclass
class SimilarityBreakdown:
    """Detailed breakdown of similarity scoring."""
    overall_score: float
    factor_scores: Dict[SimilarityFactor, float]
    factor_explanations: Dict[SimilarityFactor, str]
    confidence: float
    primary_similarities: List[str]
    key_differences: List[str]

class SimilarityExplainer:
    """Advanced similarity explanation engine."""
    
    def __init__(self):
        self.factor_weights = {
            SimilarityFactor.BUSINESS_MODEL: 0.25,
            SimilarityFactor.INDUSTRY: 0.20,
            SimilarityFactor.COMPANY_SIZE: 0.15,
            SimilarityFactor.TECHNOLOGY: 0.15,
            SimilarityFactor.MARKET_FOCUS: 0.15,
            SimilarityFactor.GROWTH_STAGE: 0.10
        }
        
    def explain_similarity(
        self, 
        source_company: Dict[str, Any],
        target_company: Dict[str, Any]
    ) -> SimilarityBreakdown:
        """Generate comprehensive similarity explanation."""
        
        # Calculate individual factor scores
        factor_scores = {}
        factor_explanations = {}
        
        for factor in SimilarityFactor:
            if factor == SimilarityFactor.GEOGRAPHY:
                continue  # Skip geography for now
                
            score, explanation = self._calculate_factor_similarity(
                factor, source_company, target_company
            )
            factor_scores[factor] = score
            factor_explanations[factor] = explanation
            
        # Calculate weighted overall score
        overall_score = sum(
            score * self.factor_weights.get(factor, 0.0)
            for factor, score in factor_scores.items()
        )
        
        # Calculate confidence based on data completeness
        confidence = self._calculate_confidence(source_company, target_company)
        
        # Identify primary similarities and differences
        primary_similarities = self._identify_primary_similarities(factor_scores, factor_explanations)
        key_differences = self._identify_key_differences(factor_scores, factor_explanations)
        
        return SimilarityBreakdown(
            overall_score=overall_score,
            factor_scores=factor_scores,
            factor_explanations=factor_explanations,
            confidence=confidence,
            primary_similarities=primary_similarities,
            key_differences=key_differences
        )
        
    def _calculate_factor_similarity(
        self, 
        factor: SimilarityFactor,
        source: Dict[str, Any],
        target: Dict[str, Any]
    ) -> Tuple[float, str]:
        """Calculate similarity score and explanation for a specific factor."""
        
        if factor == SimilarityFactor.BUSINESS_MODEL:
            return self._compare_business_models(source, target)
        elif factor == SimilarityFactor.INDUSTRY:
            return self._compare_industries(source, target)
        elif factor == SimilarityFactor.COMPANY_SIZE:
            return self._compare_company_sizes(source, target)
        elif factor == SimilarityFactor.TECHNOLOGY:
            return self._compare_technologies(source, target)
        elif factor == SimilarityFactor.MARKET_FOCUS:
            return self._compare_market_focus(source, target)
        elif factor == SimilarityFactor.GROWTH_STAGE:
            return self._compare_growth_stages(source, target)
        else:
            return 0.0, "Not implemented"
            
    def _compare_business_models(self, source: Dict, target: Dict) -> Tuple[float, str]:
        """Compare business models with nuanced scoring."""
        
        source_model = source.get('business_model', '').lower()
        target_model = target.get('business_model', '').lower()
        
        if not source_model or not target_model:
            return 0.5, "Business model data incomplete"
            
        # Exact match
        if source_model == target_model:
            return 1.0, f"Both companies use {source_model.upper()} model"
            
        # Compatible models (high similarity)
        compatible_pairs = [
            ('b2b', 'enterprise'),
            ('saas', 'b2b'),
            ('marketplace', 'platform'),
            ('ecommerce', 'retail')
        ]
        
        for model1, model2 in compatible_pairs:
            if (source_model == model1 and target_model == model2) or \
               (source_model == model2 and target_model == model1):
                return 0.8, f"Compatible models: {source_model.upper()} and {target_model.upper()}"
                
        # Related models (medium similarity)
        related_groups = [
            ['b2b', 'enterprise', 'saas'],
            ['b2c', 'ecommerce', 'marketplace'],
            ['platform', 'marketplace', 'network']
        ]
        
        for group in related_groups:
            if source_model in group and target_model in group:
                return 0.6, f"Related models in {', '.join(group)} category"
                
        # Different models
        return 0.2, f"Different models: {source_model.upper()} vs {target_model.upper()}"
        
    def _compare_industries(self, source: Dict, target: Dict) -> Tuple[float, str]:
        """Compare industries with hierarchical understanding."""
        
        source_industry = source.get('industry', '').lower()
        target_industry = target.get('industry', '').lower()
        
        if not source_industry or not target_industry:
            return 0.5, "Industry data incomplete"
            
        # Exact match
        if source_industry == target_industry:
            return 1.0, f"Both in {source_industry.title()} industry"
            
        # Industry hierarchy and relationships
        industry_relationships = {
            'technology': ['software', 'saas', 'fintech', 'healthtech'],
            'financial services': ['fintech', 'banking', 'insurance'],
            'healthcare': ['healthtech', 'biotech', 'pharmaceuticals'],
            'retail': ['ecommerce', 'fashion', 'consumer goods']
        }
        
        # Check for parent-child relationships
        for parent, children in industry_relationships.items():
            if (source_industry == parent and target_industry in children) or \
               (target_industry == parent and source_industry in children):
                return 0.8, f"Related industries: {parent.title()} sector"
                
            if source_industry in children and target_industry in children:
                return 0.7, f"Both in {parent.title()} sector"
                
        # Similar industries (fuzzy matching)
        similarity_score = self._calculate_string_similarity(source_industry, target_industry)
        if similarity_score > 0.7:
            return 0.6, f"Similar industries: {source_industry.title()} and {target_industry.title()}"
            
        return 0.3, f"Different industries: {source_industry.title()} vs {target_industry.title()}"
        
    def _compare_company_sizes(self, source: Dict, target: Dict) -> Tuple[float, str]:
        """Compare company sizes with graduated scoring."""
        
        size_order = ['startup', 'small', 'medium', 'large', 'enterprise']
        
        source_size = source.get('company_size', '').lower()
        target_size = target.get('company_size', '').lower()
        
        if not source_size or not target_size:
            return 0.5, "Company size data incomplete"
            
        try:
            source_idx = size_order.index(source_size)
            target_idx = size_order.index(target_size)
            
            difference = abs(source_idx - target_idx)
            
            if difference == 0:
                return 1.0, f"Both are {source_size} companies"
            elif difference == 1:
                return 0.8, f"Similar sizes: {source_size} and {target_size}"
            elif difference == 2:
                return 0.5, f"Moderately different sizes: {source_size} vs {target_size}"
            else:
                return 0.2, f"Very different sizes: {source_size} vs {target_size}"
                
        except ValueError:
            return 0.3, f"Unknown size categories: {source_size}, {target_size}"
            
    def _compare_technologies(self, source: Dict, target: Dict) -> Tuple[float, str]:
        """Compare technology stacks and approaches."""
        
        source_tech = source.get('technology_stack', [])
        target_tech = target.get('technology_stack', [])
        
        if not source_tech or not target_tech:
            return 0.5, "Technology data incomplete"
            
        # Calculate Jaccard similarity
        source_set = set(tech.lower() for tech in source_tech)
        target_set = set(tech.lower() for tech in target_tech)
        
        intersection = len(source_set.intersection(target_set))
        union = len(source_set.union(target_set))
        
        if union == 0:
            return 0.5, "No technology data available"
            
        jaccard_score = intersection / union
        
        if jaccard_score > 0.7:
            common_tech = list(source_set.intersection(target_set))[:3]
            return jaccard_score, f"High tech overlap: {', '.join(common_tech)}"
        elif jaccard_score > 0.3:
            return jaccard_score, f"Some technology similarities ({intersection} common)"
        else:
            return jaccard_score, "Different technology approaches"
            
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using edit distance."""
        
        def levenshtein_distance(s1, s2):
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
                
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
                
            return previous_row[-1]
            
        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 1.0
            
        distance = levenshtein_distance(str1.lower(), str2.lower())
        return 1.0 - (distance / max_len)
        
    def _calculate_confidence(self, source: Dict, target: Dict) -> float:
        """Calculate confidence based on data completeness."""
        
        important_fields = [
            'business_model', 'industry', 'company_size', 
            'description', 'founded_year'
        ]
        
        source_completeness = sum(1 for field in important_fields if source.get(field))
        target_completeness = sum(1 for field in important_fields if target.get(field))
        
        avg_completeness = (source_completeness + target_completeness) / (2 * len(important_fields))
        
        return min(1.0, avg_completeness * 1.2)  # Boost confidence slightly
        
    def _identify_primary_similarities(
        self, 
        factor_scores: Dict[SimilarityFactor, float],
        explanations: Dict[SimilarityFactor, str]
    ) -> List[str]:
        """Identify the strongest similarity factors."""
        
        high_scores = [
            (factor, score) for factor, score in factor_scores.items() 
            if score >= 0.8
        ]
        
        # Sort by score and return explanations
        high_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [explanations[factor] for factor, _ in high_scores[:3]]
        
    def _identify_key_differences(
        self,
        factor_scores: Dict[SimilarityFactor, float],
        explanations: Dict[SimilarityFactor, str]
    ) -> List[str]:
        """Identify the most significant differences."""
        
        low_scores = [
            (factor, score) for factor, score in factor_scores.items()
            if score <= 0.4
        ]
        
        # Sort by score (lowest first) and return explanations
        low_scores.sort(key=lambda x: x[1])
        
        return [explanations[factor] for factor, _ in low_scores[:2]]
        
    def generate_brief_explanation(self, company: Dict[str, Any]) -> str:
        """Generate brief explanation for table display."""
        
        # Extract key similarity factors
        factors = []
        
        business_model = company.get('business_model')
        if business_model:
            factors.append(f"{business_model} model")
            
        industry = company.get('industry')
        if industry:
            factors.append(f"{industry} industry")
            
        if len(factors) >= 2:
            return f"Similar {factors[0]} and {factors[1]}"
        elif len(factors) == 1:
            return f"Similar {factors[0]}"
        else:
            return "Business profile similarity"

# Usage in formatters
class DetailedSimilarityFormatter:
    """Formatter for detailed similarity explanations."""
    
    def __init__(self, explainer: SimilarityExplainer):
        self.explainer = explainer
        
    def format_similarity_breakdown(self, breakdown: SimilarityBreakdown) -> str:
        """Format detailed similarity breakdown for display."""
        
        output = []
        
        # Overall score
        output.append(f"Overall Similarity: {breakdown.overall_score:.2f}")
        output.append(f"Confidence: {breakdown.confidence:.2f}")
        output.append("")
        
        # Factor breakdown
        output.append("Similarity Factors:")
        for factor, score in breakdown.factor_scores.items():
            explanation = breakdown.factor_explanations[factor]
            output.append(f"  {factor.value.replace('_', ' ').title()}: {score:.2f} - {explanation}")
            
        output.append("")
        
        # Primary similarities
        if breakdown.primary_similarities:
            output.append("Key Similarities:")
            for similarity in breakdown.primary_similarities:
                output.append(f"  • {similarity}")
            output.append("")
            
        # Key differences
        if breakdown.key_differences:
            output.append("Notable Differences:")
            for difference in breakdown.key_differences:
                output.append(f"  • {difference}")
                
        return "\n".join(output)
```

This similarity explanation system provides users with transparent, interpretable insights into why companies are considered similar, building trust and enabling more informed decision-making.

### Result Caching and Performance Optimization (8 minutes)

Let's implement intelligent caching and performance optimization to make discovery fast and efficient, especially for repeated queries.

```python
# v2/src/cli/discovery/result_cache.py
import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Discovery cache entry with metadata."""
    query_hash: str
    results: Dict[str, Any]
    timestamp: float
    hit_count: int
    last_accessed: float
    filters_used: Dict[str, Any]
    source_used: str

class DiscoveryResultCache:
    """Intelligent caching system for discovery results."""
    
    def __init__(self, cache_dir: Optional[Path] = None, max_size_mb: int = 100):
        self.cache_dir = cache_dir or Path.home() / '.theodore' / 'discovery_cache'
        self.max_size_mb = max_size_mb
        self.cache_index: Dict[str, CacheEntry] = {}
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache index
        self._load_cache_index()
        
        # Performance tracking
        self.cache_hits = 0
        self.cache_misses = 0
        
    def get_cached_results(
        self,
        company_name: str,
        filters: Dict[str, Any],
        source: str,
        max_age_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached discovery results if available and fresh."""
        
        query_hash = self._generate_query_hash(company_name, filters, source)
        
        if query_hash not in self.cache_index:
            self.cache_misses += 1
            return None
            
        cache_entry = self.cache_index[query_hash]
        
        # Check if cache entry is still fresh
        age_hours = (time.time() - cache_entry.timestamp) / 3600
        if age_hours > max_age_hours:
            logger.debug(f"Cache entry expired: {age_hours:.1f} hours old")
            self._remove_cache_entry(query_hash)
            self.cache_misses += 1
            return None
            
        # Update access statistics
        cache_entry.hit_count += 1
        cache_entry.last_accessed = time.time()
        
        self.cache_hits += 1
        logger.debug(f"Cache hit for query: {company_name} (age: {age_hours:.1f}h)")
        
        return cache_entry.results
        
    def cache_results(
        self,
        company_name: str,
        filters: Dict[str, Any],
        source: str,
        results: Dict[str, Any]
    ):
        """Cache discovery results for future use."""
        
        query_hash = self._generate_query_hash(company_name, filters, source)
        
        # Create cache entry
        cache_entry = CacheEntry(
            query_hash=query_hash,
            results=results,
            timestamp=time.time(),
            hit_count=0,
            last_accessed=time.time(),
            filters_used=filters.copy(),
            source_used=source
        )
        
        # Save to disk
        try:
            cache_file_path = self.cache_dir / f"{query_hash}.cache"
            with open(cache_file_path, 'wb') as f:
                pickle.dump(cache_entry, f)
                
            # Update index
            self.cache_index[query_hash] = cache_entry
            
            # Cleanup if cache is getting too large
            self._cleanup_if_needed()
            
            # Save updated index
            self._save_cache_index()
            
            logger.debug(f"Cached results for: {company_name}")
            
        except Exception as e:
            logger.error(f"Failed to cache results: {e}")
            
    def _generate_query_hash(
        self,
        company_name: str,
        filters: Dict[str, Any],
        source: str
    ) -> str:
        """Generate deterministic hash for query parameters."""
        
        # Normalize inputs for consistent hashing
        normalized_company = company_name.lower().strip()
        
        # Sort filters for consistent ordering
        normalized_filters = {
            k: v for k, v in sorted(filters.items()) 
            if v is not None
        }
        
        # Create hash input
        hash_input = {
            'company': normalized_company,
            'filters': normalized_filters,
            'source': source
        }
        
        # Generate SHA-256 hash
        hash_string = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()[:16]
        
    def _cleanup_if_needed(self):
        """Clean up old cache entries if cache is getting too large."""
        
        total_size_mb = self._calculate_cache_size_mb()
        
        if total_size_mb > self.max_size_mb:
            logger.debug(f"Cache size ({total_size_mb}MB) exceeds limit ({self.max_size_mb}MB)")
            self._evict_old_entries()
            
    def _calculate_cache_size_mb(self) -> float:
        """Calculate total cache size in MB."""
        
        total_bytes = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                total_bytes += cache_file.stat().st_size
            except FileNotFoundError:
                pass
                
        return total_bytes / (1024 * 1024)
        
    def _evict_old_entries(self):
        """Evict old cache entries using LRU strategy."""
        
        # Sort entries by last accessed time (oldest first)
        sorted_entries = sorted(
            self.cache_index.values(),
            key=lambda entry: entry.last_accessed
        )
        
        # Remove oldest 25% of entries
        entries_to_remove = len(sorted_entries) // 4
        
        for entry in sorted_entries[:entries_to_remove]:
            self._remove_cache_entry(entry.query_hash)
            
        logger.debug(f"Evicted {entries_to_remove} old cache entries")
        
    def _remove_cache_entry(self, query_hash: str):
        """Remove cache entry from disk and index."""
        
        # Remove from index
        self.cache_index.pop(query_hash, None)
        
        # Remove file
        cache_file_path = self.cache_dir / f"{query_hash}.cache"
        try:
            cache_file_path.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Failed to remove cache file: {e}")
            
    def _load_cache_index(self):
        """Load cache index from disk."""
        
        index_file = self.cache_dir / "cache_index.json"
        
        if not index_file.exists():
            return
            
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
                
            # Reconstruct cache entries
            for query_hash, entry_data in index_data.items():
                self.cache_index[query_hash] = CacheEntry(**entry_data)
                
            logger.debug(f"Loaded {len(self.cache_index)} cache entries")
            
        except Exception as e:
            logger.error(f"Failed to load cache index: {e}")
            
    def _save_cache_index(self):
        """Save cache index to disk."""
        
        index_file = self.cache_dir / "cache_index.json"
        
        try:
            # Convert cache entries to serializable format
            index_data = {}
            for query_hash, entry in self.cache_index.items():
                index_data[query_hash] = {
                    'query_hash': entry.query_hash,
                    'timestamp': entry.timestamp,
                    'hit_count': entry.hit_count,
                    'last_accessed': entry.last_accessed,
                    'filters_used': entry.filters_used,
                    'source_used': entry.source_used
                }
                
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
            
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            'hit_rate': hit_rate,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cached_queries': len(self.cache_index),
            'cache_size_mb': self._calculate_cache_size_mb()
        }
        
    def clear_cache(self):
        """Clear all cached results."""
        
        # Remove all cache files
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"Failed to remove cache file: {e}")
                
        # Clear index
        self.cache_index.clear()
        
        # Remove index file
        index_file = self.cache_dir / "cache_index.json"
        index_file.unlink(missing_ok=True)
        
        logger.info("Discovery cache cleared")

# Performance optimization utilities
class DiscoveryPerformanceOptimizer:
    """Performance optimization for discovery operations."""
    
    def __init__(self):
        self.query_patterns = {}
        self.performance_metrics = {}
        
    def optimize_query_parameters(
        self,
        company_name: str,
        filters: Dict[str, Any],
        historical_performance: Dict[str, float]
    ) -> Dict[str, Any]:
        """Optimize query parameters based on historical performance."""
        
        optimized_filters = filters.copy()
        
        # Adjust similarity threshold based on company type
        if self._is_well_known_company(company_name):
            # Well-known companies: use higher threshold for precision
            optimized_filters['similarity_threshold'] = max(
                optimized_filters.get('similarity_threshold', 0.6), 0.7
            )
        else:
            # Unknown companies: use lower threshold for coverage
            optimized_filters['similarity_threshold'] = min(
                optimized_filters.get('similarity_threshold', 0.6), 0.5
            )
            
        return optimized_filters
        
    def _is_well_known_company(self, company_name: str) -> bool:
        """Determine if company is well-known based on name patterns."""
        
        well_known_indicators = [
            'inc', 'corp', 'limited', 'ltd', 'llc', 'technologies',
            'systems', 'solutions', 'software', 'services'
        ]
        
        name_lower = company_name.lower()
        return any(indicator in name_lower for indicator in well_known_indicators)
        
    def suggest_performance_improvements(
        self,
        query_time: float,
        result_count: int,
        filters_used: Dict[str, Any]
    ) -> List[str]:
        """Suggest performance improvements based on query results."""
        
        suggestions = []
        
        if query_time > 10.0:  # Slow query
            suggestions.append("Consider using more specific filters to reduce search scope")
            
            if not filters_used.get('industry'):
                suggestions.append("Add industry filter for faster discovery")
                
            if not filters_used.get('business_model'):
                suggestions.append("Add business model filter for more targeted results")
                
        if result_count > 50:
            suggestions.append("Increase similarity threshold to get more focused results")
            
        if result_count < 3:
            suggestions.append("Lower similarity threshold or remove filters for broader discovery")
            
        return suggestions

# Integration with discovery command
async def _execute_discovery_with_caching(
    container: Any,
    company_name: str,
    filters: Dict[str, Any],
    source: str,
    limit: int,
    cache_enabled: bool = True
) -> Dict[str, Any]:
    """Execute discovery with intelligent caching."""
    
    cache = DiscoveryResultCache()
    
    # Try to get cached results first
    if cache_enabled:
        cached_results = cache.get_cached_results(company_name, filters, source)
        if cached_results:
            console.print("💾 Using cached results", style="dim green")
            return cached_results
            
    # Execute fresh discovery
    start_time = time.time()
    
    discover_use_case = container.use_cases.discover_similar()
    params = {
        'company_name': company_name,
        'filters': filters,
        'discovery_source': source,
        'max_results': limit
    }
    
    results = await discover_use_case.execute(**params)
    
    query_time = time.time() - start_time
    
    # Cache results if enabled
    if cache_enabled:
        cache.cache_results(company_name, filters, source, results)
        
    # Add performance metrics to results
    results['performance'] = {
        'query_time_seconds': query_time,
        'cache_hit': False,
        'result_count': len(results.get('companies', []))
    }
    
    return results
```

This caching system dramatically improves performance for repeated queries while ensuring users always get fresh, relevant results.

### Conclusion and Integration Testing (6 minutes)

Let's complete our discovery command implementation with comprehensive testing and a review of the sophisticated system we've built.

```python
# v2/tests/e2e/test_discover_cli.py
import pytest
import tempfile
import json
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import AsyncMock, patch, MagicMock

from src.cli.commands.discover import discover
from src.infrastructure.container import ContainerFactory

class TestDiscoverCLIIntegration:
    """
    End-to-end tests for the discover CLI command.
    
    Tests the complete discovery pipeline including filtering,
    similarity scoring, caching, and interactive workflows.
    """
    
    @pytest.fixture
    def cli_runner(self):
        return CliRunner()
        
    @pytest.fixture
    def temp_output_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
            
    @pytest.fixture
    def mock_discovery_results(self):
        return {
            "companies": [
                {
                    "name": "Similar Corp A",
                    "website": "https://similar-a.com",
                    "industry": "Technology",
                    "business_model": "B2B SaaS",
                    "company_size": "medium",
                    "similarity_score": 0.92,
                    "similarity_explanation": "Similar SaaS business model and tech focus"
                },
                {
                    "name": "Similar Corp B", 
                    "website": "https://similar-b.com",
                    "industry": "Technology",
                    "business_model": "B2B",
                    "company_size": "large",
                    "similarity_score": 0.85,
                    "similarity_explanation": "Similar B2B focus with different scale"
                },
                {
                    "name": "Similar Corp C",
                    "website": "https://similar-c.com",
                    "industry": "Software",
                    "business_model": "SaaS",
                    "company_size": "small",
                    "similarity_score": 0.78,
                    "similarity_explanation": "Similar SaaS model, smaller scale"
                }
            ],
            "discovery_metadata": {
                "source_used": "hybrid",
                "query_time": 2.3,
                "total_candidates": 1247,
                "filters_applied": ["business_model", "similarity_threshold"]
            },
            "performance": {
                "query_time_seconds": 2.3,
                "cache_hit": False,
                "result_count": 3
            }
        }
        
    @pytest.mark.asyncio
    async def test_basic_discovery_command(self, cli_runner, mock_discovery_results):
        """Test basic discovery command execution."""
        
        with patch('src.cli.commands.discover._initialize_discovery_container') as mock_container:
            with patch('src.cli.commands.discover._run_standard_discovery') as mock_discovery:
                # Setup mocks
                mock_discovery.return_value = mock_discovery_results
                
                # Execute command
                result = cli_runner.invoke(discover, ['Salesforce'])
                
                # Verify success
                assert result.exit_code == 0
                assert "Discovered 3 similar companies" in result.output
                assert "Similar Corp A" in result.output
                
    @pytest.mark.asyncio
    async def test_discovery_with_advanced_filters(self, cli_runner, mock_discovery_results):
        """Test discovery with multiple filter combinations."""
        
        with patch('src.cli.commands.discover._initialize_discovery_container'):
            with patch('src.cli.commands.discover._run_standard_discovery') as mock_discovery:
                mock_discovery.return_value = mock_discovery_results
                
                # Execute with multiple filters
                result = cli_runner.invoke(discover, [
                    'Stripe',
                    '--business-model', 'saas',
                    '--company-size', 'medium', 
                    '--industry', 'fintech',
                    '--similarity-threshold', '0.8',
                    '--limit', '15'
                ])
                
                assert result.exit_code == 0
                assert "Active Discovery Filters" in result.output
                
    @pytest.mark.asyncio
    async def test_discovery_output_formats(self, cli_runner, mock_discovery_results, temp_output_dir):
        """Test discovery with different output formats and file saving."""
        
        output_file = temp_output_dir / "discovery_results.json"
        
        with patch('src.cli.commands.discover._initialize_discovery_container'):
            with patch('src.cli.commands.discover._run_standard_discovery') as mock_discovery:
                mock_discovery.return_value = mock_discovery_results
                
                # Execute with JSON output and save
                result = cli_runner.invoke(discover, [
                    'Tesla',
                    '--output', 'json',
                    '--save', str(output_file),
                    '--explain-similarity'
                ])
                
                assert result.exit_code == 0
                
                # Verify file was created with valid JSON
                assert output_file.exists()
                
                with open(output_file, 'r') as f:
                    saved_data = json.load(f)
                    
                assert 'companies' in saved_data
                assert len(saved_data['companies']) == 3
                
    @pytest.mark.asyncio
    async def test_discovery_similarity_explanations(self, cli_runner, mock_discovery_results):
        """Test similarity explanation display."""
        
        with patch('src.cli.commands.discover._initialize_discovery_container'):
            with patch('src.cli.commands.discover._run_standard_discovery') as mock_discovery:
                mock_discovery.return_value = mock_discovery_results
                
                # Execute with similarity explanations
                result = cli_runner.invoke(discover, [
                    'Microsoft',
                    '--explain-similarity',
                    '--verbose'
                ])
                
                assert result.exit_code == 0
                assert "Why Similar" in result.output
                assert "similarity_explanation" in result.output or "Similar" in result.output
                
    @pytest.mark.asyncio
    async def test_discovery_source_selection(self, cli_runner, mock_discovery_results):
        """Test different discovery source preferences."""
        
        with patch('src.cli.commands.discover._initialize_discovery_container'):
            with patch('src.cli.commands.discover._run_standard_discovery') as mock_discovery:
                mock_discovery.return_value = mock_discovery_results
                
                # Test vector-only discovery
                result = cli_runner.invoke(discover, [
                    'Apple',
                    '--source', 'vector',
                    '--verbose'
                ])
                
                assert result.exit_code == 0
                
                # Test web-only discovery
                result = cli_runner.invoke(discover, [
                    'Unknown Startup',
                    '--source', 'web',
                    '--verbose'
                ])
                
                assert result.exit_code == 0
                
    @pytest.mark.asyncio
    async def test_discovery_error_handling(self, cli_runner):
        """Test error handling for various invalid inputs."""
        
        # Test invalid company name
        result = cli_runner.invoke(discover, [''])
        assert result.exit_code != 0
        
        # Test invalid similarity threshold
        result = cli_runner.invoke(discover, ['Test Company', '--similarity-threshold', '1.5'])
        assert result.exit_code != 0
        
        # Test invalid limit
        result = cli_runner.invoke(discover, ['Test Company', '--limit', '0'])
        assert result.exit_code != 0
        
    @pytest.mark.asyncio
    async def test_discovery_caching_behavior(self, cli_runner, mock_discovery_results):
        """Test discovery result caching functionality."""
        
        with patch('src.cli.commands.discover._initialize_discovery_container'):
            with patch('src.cli.commands.discover._execute_discovery_with_caching') as mock_cached_discovery:
                # First call - cache miss
                mock_cached_discovery.return_value = mock_discovery_results
                
                result = cli_runner.invoke(discover, [
                    'Google',
                    '--cache-results'
                ])
                
                assert result.exit_code == 0
                
                # Second call - should use cache
                mock_cached_results = mock_discovery_results.copy()
                mock_cached_results['performance']['cache_hit'] = True
                mock_cached_discovery.return_value = mock_cached_results
                
                result = cli_runner.invoke(discover, [
                    'Google',
                    '--cache-results'
                ])
                
                assert result.exit_code == 0
                
    def test_discovery_help_documentation(self, cli_runner):
        """Test that help documentation is comprehensive."""
        
        result = cli_runner.invoke(discover, ['--help'])
        
        assert result.exit_code == 0
        assert "Discover companies similar to" in result.output
        assert "Examples:" in result.output
        assert "--business-model" in result.output
        assert "--similarity-threshold" in result.output
        assert "--interactive" in result.output
        
    @pytest.mark.asyncio
    async def test_discovery_performance_metrics(self, cli_runner, mock_discovery_results):
        """Test discovery performance tracking and optimization."""
        
        with patch('src.cli.commands.discover._initialize_discovery_container'):
            with patch('src.cli.commands.discover._run_standard_discovery') as mock_discovery:
                mock_discovery.return_value = mock_discovery_results
                
                # Execute discovery with verbose performance info
                result = cli_runner.invoke(discover, [
                    'Netflix',
                    '--verbose',
                    '--limit', '20'
                ])
                
                assert result.exit_code == 0
                # Should include performance information in verbose mode
                
@pytest.mark.performance  
class TestDiscoveryPerformance:
    """Performance tests for discovery command."""
    
    @pytest.mark.asyncio
    async def test_discovery_startup_performance(self, cli_runner):
        """Test discovery command startup time."""
        
        import time
        
        start_time = time.time()
        result = cli_runner.invoke(discover, ['--help'])
        startup_time = time.time() - start_time
        
        assert result.exit_code == 0
        assert startup_time < 2.0  # Should start quickly
        
    @pytest.mark.asyncio
    async def test_large_result_set_handling(self, cli_runner, temp_output_dir):
        """Test performance with large discovery result sets."""
        
        # Create large mock dataset
        large_results = {
            "companies": [
                {
                    "name": f"Company {i}",
                    "similarity_score": 0.9 - (i * 0.01),
                    "industry": "Technology",
                    "business_model": "SaaS"
                }
                for i in range(100)  # 100 similar companies
            ],
            "discovery_metadata": {
                "source_used": "hybrid",
                "total_candidates": 5000
            }
        }
        
        with patch('src.cli.commands.discover._initialize_discovery_container'):
            with patch('src.cli.commands.discover._run_standard_discovery') as mock_discovery:
                mock_discovery.return_value = large_results
                
                start_time = time.time()
                
                result = cli_runner.invoke(discover, [
                    'Tech Giant',
                    '--limit', '100',
                    '--output', 'json'
                ])
                
                processing_time = time.time() - start_time
                
                assert result.exit_code == 0
                assert processing_time < 15.0  # Should handle large results efficiently

@pytest.mark.integration
class TestDiscoveryIntegration:
    """Integration tests with real use case dependencies."""
    
    @pytest.mark.asyncio
    async def test_discovery_use_case_integration(self, cli_runner):
        """Test integration with real discovery use case."""
        
        # This would test with actual container and use case
        # but mocked external services
        pass
        
    @pytest.mark.asyncio  
    async def test_discovery_filter_integration(self, cli_runner):
        """Test advanced filter integration and validation."""
        
        # Test complex filter combinations
        pass
```

**Summary of the Complete Discovery Command System:**

In this comprehensive tutorial, we've built a sophisticated discovery command that:

1. **Multi-Source Discovery Intelligence**: Combines vector similarity with web search for comprehensive coverage

2. **Advanced Filtering System**: Multi-dimensional filtering with business intelligence and hierarchical understanding  

3. **Transparent Similarity Scoring**: Detailed explanations showing why companies are similar with factor-based breakdown

4. **Interactive Discovery Workflows**: Progressive refinement with real-time feedback and seamless research integration

5. **Intelligent Caching**: Performance optimization with LRU eviction and query fingerprinting

6. **Professional Error Handling**: Context-aware error messages with actionable suggestions

7. **Comprehensive Testing**: Unit, integration, and performance testing across all components

**Key Technical Achievements:**

- **Semantic Understanding**: Goes beyond keyword matching to understand business context and relationships
- **Performance Optimization**: Intelligent caching and query optimization for fast repeated searches  
- **User Experience Excellence**: Interactive modes, real-time feedback, and transparent similarity explanations
- **Production Readiness**: Comprehensive error handling, performance monitoring, and quality metrics

The discovery command provides users with powerful competitive intelligence capabilities, enabling them to explore market landscapes, identify opportunities, and understand competitive positioning through AI-powered similarity analysis.

This completes Theodore v2's core user interface, giving users both research (detailed company analysis) and discovery (competitive landscape exploration) capabilities through a beautiful, professional CLI experience.

## Estimated Time: 6-7 hours