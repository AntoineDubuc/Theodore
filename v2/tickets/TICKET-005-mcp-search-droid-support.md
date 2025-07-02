# TICKET-005: MCP Search Droid Support

## Overview
Enhance domain models and create infrastructure to support pluggable MCP (Model Context Protocol) search droids, allowing users to configure and use custom search tools for company discovery.

## Problem Statement
Currently, the similarity discovery system only supports hardcoded search methods (Google Search, Vector Search, etc.). Users cannot plug in their own MCP-compatible search tools like Perplexity, Tavily, or custom enterprise search APIs.

## Acceptance Criteria
- [ ] Domain models support MCP tool metadata and configuration
- [ ] MCP tool registry for managing available tools
- [ ] Port definition for MCP search tools
- [ ] Adapter pattern implementation for MCP tools
- [ ] Configuration system for tool-specific settings
- [ ] Result aggregation from multiple MCP tools
- [ ] Tool performance tracking and metrics
- [ ] Tests with mock MCP tools

## Technical Details

### Domain Model Updates
1. Add `MCP_TOOL` to `SimilarityMethod` enum
2. Create `MCPToolInfo` value object
3. Enhance `SimilarCompany` with MCP metadata
4. Add MCP tool tracking to `SimilarityResult`
5. Add MCP configuration to `Research` entity

### New Components
1. **MCP Tool Port** (`v2/src/core/ports/mcp_search_tool.py`)
   - Interface for all MCP search tools
   - Standard input/output contracts
   - Error handling requirements

2. **MCP Tool Registry** (`v2/src/core/domain/services/mcp_registry.py`)
   - Register available tools
   - Validate tool capabilities
   - Manage tool lifecycle

3. **MCP Result Aggregator** (`v2/src/core/domain/services/mcp_aggregator.py`)
   - Combine results from multiple tools
   - Deduplicate companies
   - Merge confidence scores

4. **Base MCP Adapter** (`v2/src/infrastructure/adapters/mcp/base_adapter.py`)
   - Common functionality for all MCP adapters
   - Error handling and retry logic
   - Metric collection

## Implementation Plan

### Phase 1: Domain Model Enhancement
Update existing models with MCP support fields and methods.

### Phase 2: Port and Registry
Create the port interface and registry system for tool management.

### Phase 3: Base Infrastructure
Implement base adapter and aggregator services.

### Phase 4: Example Implementations
Create 2-3 example MCP tool adapters (Perplexity, Tavily, etc.).

### Phase 5: Integration
Update use cases to support MCP tool selection and configuration.

## Testing Strategy
- Unit tests for all new domain logic
- Integration tests with mock MCP tools
- Performance tests with multiple tools
- Configuration validation tests

## Example Usage

```python
# Configure MCP tools for research
research = Research(
    company_name="Stripe",
    source=ResearchSource.CLI,
    enabled_mcp_tools=["perplexity_search", "tavily_api"],
    mcp_tool_configs={
        "perplexity_search": {
            "model": "sonar-medium",
            "search_depth": "comprehensive"
        },
        "tavily_api": {
            "search_depth": 2,
            "include_domains": ["techcrunch.com", "bloomberg.com"]
        }
    }
)

# Discovery with MCP tools
result = discover_similar_companies(
    company_name="Stripe",
    mcp_tools=[
        MCPToolInfo(
            tool_name="perplexity_search",
            tool_version="1.0",
            capabilities=["web_search", "news_search", "company_data"]
        )
    ]
)

# Results include tool attribution
for company in result.similar_companies:
    print(f"{company.name} found by {company.mcp_tool_used.tool_name}")
```

## Estimated Time: 6-8 hours

## Dependencies

### Core Domain Dependencies
- **TICKET-001 (Core Domain Models)** - Required for domain model enhancements
  - Provides existing `SimilarityMethod` enum that needs MCP_TOOL addition
  - Contains `SimilarCompany` entity that requires MCP metadata fields
  - Includes `SimilarityResult` aggregation that needs MCP tool tracking
  - Files: `v2/src/core/domain/entities/similarity.py`, `v2/src/core/domain/entities/research.py`

### Configuration Infrastructure Dependencies
- **TICKET-003 (Configuration System)** - Required for MCP tool configurations
  - Provides secure configuration loading for MCP tool API keys
  - Manages tool-specific settings and capabilities registration
  - Handles per-tool configuration validation and defaults
  - Files: `v2/src/core/config/settings.py`, `v2/src/core/config/mcp_settings.py`

### Progress and Monitoring Dependencies
- **TICKET-004 (Progress Tracking Port)** - Required for search progress tracking
  - Provides progress tracking interface for MCP search operations
  - Enables real-time feedback during multi-tool search execution
  - Supports cancellation and timeout handling for long-running searches
  - Files: `v2/src/core/ports/progress_tracker.py`

### Use Case Integration Dependencies
- **TICKET-011 (DiscoverSimilar Use Case)** - Required for MCP tool integration
  - Needs enhancement to support MCP tool selection and execution
  - Must integrate with MCP registry and result aggregation services
  - Requires modification to handle multiple search source coordination
  - Files: `v2/src/core/use_cases/discover_similar_companies.py`

### Testing Framework Dependencies
- **TICKET-027 (Testing Framework)** - Needed for comprehensive MCP testing
  - Provides mock framework for external MCP tool APIs
  - Enables integration testing with real MCP services
  - Supports performance testing for multi-tool scenarios
  - Files: `v2/tests/fixtures/`, `v2/tests/mocks/`

### Observability Dependencies (Future)
- **TICKET-026 (Observability System)** - Needed for MCP tool monitoring
  - Provides performance metrics collection for MCP tools
  - Enables cost tracking per MCP tool usage
  - Supports health monitoring and availability tracking
  - Files: `v2/src/infrastructure/monitoring/`

## Files to Create
- `v2/src/core/ports/mcp_search_tool.py`
- `v2/src/core/domain/services/mcp_registry.py`
- `v2/src/core/domain/services/mcp_aggregator.py`
- `v2/src/infrastructure/adapters/mcp/base_adapter.py`
- `v2/src/infrastructure/adapters/mcp/perplexity_adapter.py`
- `v2/src/infrastructure/adapters/mcp/tavily_adapter.py`
- `v2/tests/unit/domain/test_mcp_registry.py`
- `v2/tests/unit/domain/test_mcp_aggregator.py`
- `v2/tests/integration/test_mcp_tools.py`

## Notes
- Follow the same port/adapter pattern as other integrations
- Ensure backward compatibility with existing search methods
- Consider rate limiting and cost tracking per tool
- Document tool-specific configuration options

---

# Udemy Tutorial Script: Building MCP Search Droid Support

## Introduction (2 minutes)

**[SLIDE 1: Title - "Building Extensible Search with MCP"]**

"Hello and welcome! I'm excited to guide you through implementing MCP Search Droid Support in Theodore's AI Company Intelligence System. 

By the end of this tutorial, you'll understand how to build a plugin architecture that allows users to bring their own AI-powered search tools. This is a game-changer because it means your application isn't locked into one search provider - users can plug in Perplexity, Tavily, or even their own custom enterprise search tools.

Let's dive in!"

## Section 1: Understanding the Problem (3 minutes)

**[SLIDE 2: The Limitation]**

"Before we start coding, let's understand why this matters. Currently, most applications hard-code their search providers. Look at this code:

```python
# ❌ The OLD way - hardcoded search
def search_similar_companies(company_name):
    if use_google:
        return google_search(company_name)
    else:
        return bing_search(company_name)
```

See the problem? Every time you want to add a new search provider, you need to modify your core code. That's not scalable!

**[SLIDE 3: The Solution - MCP]**

With MCP (Model Context Protocol), we're building something like this:

```python
# ✅ The NEW way - plugin architecture
def search_similar_companies(company_name, mcp_tools):
    results = []
    for tool in mcp_tools:
        results.extend(tool.search(company_name))
    return aggregate_results(results)
```

Now users can bring ANY MCP-compatible search tool. Let's build this!"

## Section 2: Updating Domain Models (10 minutes)

**[SLIDE 4: Domain Model Updates]**

"First, we need to update our domain models to support MCP tools. Open your code editor and let's start with the SimilarityMethod enum.

```python
# In v2/src/core/domain/entities/similarity.py

class SimilarityMethod(str, Enum):
    """How similarity was determined"""
    VECTOR_SEARCH = "vector_search"
    GOOGLE_SEARCH = "google_search"
    LLM_SUGGESTION = "llm_suggestion"
    HYBRID = "hybrid"
    MANUAL = "manual"
    MCP_TOOL = "mcp_tool"  # 🆕 Add this line!
```

Great! Now let's create a new value object to store MCP tool information:

```python
class MCPToolInfo(BaseModel):
    """Information about MCP tool used for discovery"""
    tool_name: str = Field(..., description="MCP tool name")
    tool_version: Optional[str] = Field(None, description="Tool version")
    tool_config: Dict[str, Any] = Field(default_factory=dict)
    capabilities: List[str] = Field(default_factory=list)
    
    # Add a method to check capabilities
    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities
```

**[PAUSE POINT]** "Take a moment to add these to your code. Notice how we're using Pydantic for validation - this ensures tool names are always provided."

**[SLIDE 5: Enhancing SimilarCompany]**

"Now let's update the SimilarCompany model to track which MCP tool found it:

```python
class SimilarCompany(BaseModel):
    # ... existing fields ...
    
    # 🆕 MCP-specific fields
    mcp_tool_used: Optional[MCPToolInfo] = Field(None)
    mcp_confidence: Optional[float] = Field(None)
    mcp_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def was_found_by_mcp(self) -> bool:
        """Check if this company was found by an MCP tool"""
        return self.mcp_tool_used is not None
```

**[SLIDE 6: Updating SimilarityResult]**

"The SimilarityResult needs to track all MCP tools used:

```python
class SimilarityResult(BaseModel):
    # ... existing fields ...
    
    # 🆕 MCP support
    mcp_tools_used: List[MCPToolInfo] = Field(default_factory=list)
    mcp_tool_results: Dict[str, List[str]] = Field(default_factory=dict)
    
    def add_mcp_discovery(self, tool_info: MCPToolInfo, 
                         companies: List[SimilarCompany]):
        """Add companies discovered by an MCP tool"""
        # Track the tool
        if tool_info not in self.mcp_tools_used:
            self.mcp_tools_used.append(tool_info)
        
        # Track which companies came from which tool
        company_ids = []
        for company in companies:
            company.mcp_tool_used = tool_info
            company.discovery_method = SimilarityMethod.MCP_TOOL
            self.add_company(company)
            if company.id:
                company_ids.append(company.id)
        
        self.mcp_tool_results[tool_info.tool_name] = company_ids
```

**[INTERACTIVE MOMENT]** "Pause the video and implement these changes. Make sure your code compiles before continuing!"

## Section 3: Creating the MCP Port (8 minutes)

**[SLIDE 7: Port Interface]**

"Now for the exciting part - creating the port interface that all MCP tools will implement. This is the contract that makes our plugin system work!

Create a new file `v2/src/core/ports/mcp_search_tool.py`:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from v2.src.core.domain.entities.similarity import SimilarCompany, MCPToolInfo

class MCPSearchTool(ABC):
    """Port interface for MCP search tools"""
    
    @abstractmethod
    def get_tool_info(self) -> MCPToolInfo:
        """Return information about this tool"""
        pass
    
    @abstractmethod
    async def search_similar_companies(
        self, 
        company_name: str,
        company_website: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SimilarCompany]:
        """Search for similar companies using this tool"""
        pass
    
    @abstractmethod
    async def validate_configuration(self) -> bool:
        """Validate the tool is properly configured"""
        pass
    
    @abstractmethod
    def estimate_cost(self, query_count: int) -> float:
        """Estimate the cost of running queries"""
        pass
```

**[SLIDE 8: Understanding the Port Pattern]**

"Let me explain why this is powerful. By defining this interface:
1. Any tool that implements these methods can be used
2. We don't care HOW they search, just that they return SimilarCompany objects
3. Tools can estimate costs upfront
4. We can validate configuration before use

This is the Open/Closed Principle in action - our system is open for extension but closed for modification!"

## Section 4: Building the MCP Registry (10 minutes)

**[SLIDE 9: The Registry Pattern]**

"Now we need a way to manage all available MCP tools. Let's create a registry:

```python
# v2/src/core/domain/services/mcp_registry.py

from typing import Dict, List, Optional
import asyncio

class MCPToolRegistry:
    """Registry for managing MCP search tools"""
    
    def __init__(self):
        self._tools: Dict[str, MCPSearchTool] = {}
        self._default_tool: Optional[str] = None
    
    def register_tool(self, tool: MCPSearchTool) -> None:
        """Register a new MCP tool"""
        tool_info = tool.get_tool_info()
        
        # Validate before registering
        if not asyncio.run(tool.validate_configuration()):
            raise ValueError(f"Tool {tool_info.tool_name} failed validation")
        
        self._tools[tool_info.tool_name] = tool
        print(f"✅ Registered MCP tool: {tool_info.tool_name}")
    
    def get_tool(self, tool_name: str) -> MCPSearchTool:
        """Get a specific tool by name"""
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' not found. Available: {list(self._tools.keys())}")
        return self._tools[tool_name]
    
    def get_all_tools(self) -> List[MCPSearchTool]:
        """Get all registered tools"""
        return list(self._tools.values())
    
    def set_default_tool(self, tool_name: str) -> None:
        """Set the default tool for searches"""
        if tool_name not in self._tools:
            raise KeyError(f"Cannot set default: tool '{tool_name}' not registered")
        self._default_tool = tool_name
    
    def get_tools_with_capability(self, capability: str) -> List[MCPSearchTool]:
        """Find all tools with a specific capability"""
        matching_tools = []
        for tool in self._tools.values():
            if tool.get_tool_info().has_capability(capability):
                matching_tools.append(tool)
        return matching_tools
```

**[SLIDE 10: Registry Usage]**

"Here's how we'll use the registry in practice:

```python
# Initialize the registry
registry = MCPToolRegistry()

# Register tools (we'll build these next)
registry.register_tool(PerplexitySearchTool(api_key="..."))
registry.register_tool(TavilySearchTool(api_key="..."))
registry.register_tool(CustomEnterpriseSearchTool(endpoint="..."))

# Set a default
registry.set_default_tool("perplexity_search")

# Find tools with specific capabilities
news_tools = registry.get_tools_with_capability("news_search")
```

**[QUIZ MOMENT]** "Quick quiz: Why do we validate configuration before registering a tool? Pause and think about it... That's right! We want to fail fast if a tool isn't properly configured."

## Section 5: Creating the Result Aggregator (8 minutes)

**[SLIDE 11: Aggregating Results]**

"When using multiple MCP tools, we need to intelligently combine their results. Let's build an aggregator:

```python
# v2/src/core/domain/services/mcp_aggregator.py

class MCPResultAggregator:
    """Aggregates results from multiple MCP tools"""
    
    def __init__(self):
        self.deduplication_threshold = 0.9  # Similarity threshold for dedup
    
    def aggregate_results(
        self,
        results_by_tool: Dict[str, List[SimilarCompany]]
    ) -> List[SimilarCompany]:
        """Aggregate and deduplicate results from multiple tools"""
        
        # Collect all companies
        all_companies = []
        for tool_name, companies in results_by_tool.items():
            all_companies.extend(companies)
        
        # Deduplicate by name and website
        seen = {}
        deduplicated = []
        
        for company in all_companies:
            # Create a key for deduplication
            key = self._create_company_key(company)
            
            if key not in seen:
                seen[key] = company
                deduplicated.append(company)
            else:
                # Merge information from duplicate
                self._merge_company_data(seen[key], company)
        
        # Sort by confidence
        deduplicated.sort(
            key=lambda c: c.mcp_confidence or 0.5, 
            reverse=True
        )
        
        return deduplicated
    
    def _create_company_key(self, company: SimilarCompany) -> str:
        """Create a unique key for deduplication"""
        # Use normalized name and domain
        name = company.name.lower().strip()
        domain = ""
        if company.website:
            # Extract domain from URL
            domain = company.website.lower()
            domain = domain.replace("https://", "").replace("http://", "")
            domain = domain.split("/")[0]
        
        return f"{name}|{domain}"
    
    def _merge_company_data(self, target: SimilarCompany, source: SimilarCompany):
        """Merge data from source into target"""
        # Keep the higher confidence
        if source.mcp_confidence and target.mcp_confidence:
            target.mcp_confidence = max(source.mcp_confidence, target.mcp_confidence)
        
        # Merge metadata
        target.mcp_metadata.update(source.mcp_metadata)
        
        # Add tool to metadata to track all sources
        if "found_by_tools" not in target.mcp_metadata:
            target.mcp_metadata["found_by_tools"] = []
        
        if source.mcp_tool_used:
            target.mcp_metadata["found_by_tools"].append(source.mcp_tool_used.tool_name)
```

**[PRACTICAL TIP]** "Notice the deduplication logic - we normalize company names and extract domains. This handles cases where different tools return 'Stripe Inc.' vs 'Stripe' vs 'stripe.com'."

## Section 6: Building a Real MCP Adapter (12 minutes)

**[SLIDE 12: Perplexity Adapter]**

"Let's build a real adapter for Perplexity AI. This shows how to implement the MCP port:

```python
# v2/src/infrastructure/adapters/mcp/perplexity_adapter.py

import aiohttp
from typing import List, Dict, Any, Optional
import os

class PerplexitySearchTool(MCPSearchTool):
    """MCP adapter for Perplexity AI search"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai"
        self.model = "sonar-medium-online"
    
    def get_tool_info(self) -> MCPToolInfo:
        return MCPToolInfo(
            tool_name="perplexity_search",
            tool_version="1.0",
            capabilities=[
                "web_search",
                "news_search", 
                "company_research",
                "real_time_data"
            ],
            tool_config={
                "model": self.model,
                "search_recency": "month"
            }
        )
    
    async def search_similar_companies(
        self,
        company_name: str,
        company_website: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SimilarCompany]:
        
        # Build the search query
        query = self._build_search_query(company_name, company_website, filters)
        
        # Call Perplexity API
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": query
                }],
                "search_recency_filter": "month",
                "return_citations": True,
                "temperature": 0.2
            }
            
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                data = await response.json()
        
        # Parse results
        return self._parse_perplexity_response(data, limit)
    
    def _build_search_query(
        self, 
        company_name: str,
        website: Optional[str],
        filters: Optional[Dict[str, Any]]
    ) -> str:
        """Build an effective search query for Perplexity"""
        
        query_parts = [
            f"Find companies similar to {company_name}",
            f"that compete with or are alternatives to {company_name}"
        ]
        
        if website:
            query_parts.append(f"(website: {website})")
        
        if filters:
            if "industry" in filters:
                query_parts.append(f"in the {filters['industry']} industry")
            if "company_size" in filters:
                query_parts.append(f"with {filters['company_size']} employees")
            if "location" in filters:
                query_parts.append(f"located in {filters['location']}")
        
        query_parts.extend([
            "Return as a list with:",
            "- Company name",
            "- Website URL", 
            "- Brief description",
            "- Why they are similar",
            f"Limit to {limit} most relevant companies"
        ])
        
        return " ".join(query_parts)
    
    def _parse_perplexity_response(
        self, 
        response_data: Dict[str, Any],
        limit: int
    ) -> List[SimilarCompany]:
        """Parse Perplexity API response into SimilarCompany objects"""
        
        companies = []
        
        try:
            content = response_data["choices"][0]["message"]["content"]
            citations = response_data.get("citations", [])
            
            # Parse the content (this is simplified - in reality you'd use better parsing)
            lines = content.split("\n")
            current_company = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith("- Company:"):
                    if current_company:
                        companies.append(self._create_company(current_company))
                    current_company = {"name": line.replace("- Company:", "").strip()}
                elif line.startswith("- Website:"):
                    current_company["website"] = line.replace("- Website:", "").strip()
                elif line.startswith("- Description:"):
                    current_company["description"] = line.replace("- Description:", "").strip()
                elif line.startswith("- Similar because:"):
                    current_company["reasoning"] = line.replace("- Similar because:", "").strip()
            
            # Don't forget the last company
            if current_company:
                companies.append(self._create_company(current_company))
                
        except Exception as e:
            print(f"Error parsing Perplexity response: {e}")
        
        return companies[:limit]
    
    def _create_company(self, data: Dict[str, Any]) -> SimilarCompany:
        """Create a SimilarCompany from parsed data"""
        return SimilarCompany(
            name=data.get("name", "Unknown"),
            website=data.get("website"),
            description=data.get("description"),
            discovery_method=SimilarityMethod.MCP_TOOL,
            mcp_tool_used=self.get_tool_info(),
            mcp_confidence=0.8,  # Perplexity is generally high quality
            mcp_metadata={
                "reasoning": data.get("reasoning", ""),
                "search_model": self.model
            }
        )
    
    async def validate_configuration(self) -> bool:
        """Validate Perplexity API key works"""
        if not self.api_key:
            return False
        
        try:
            # Make a simple test request
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers
                ) as response:
                    return response.status == 200
        except:
            return False
    
    def estimate_cost(self, query_count: int) -> float:
        """Estimate cost based on Perplexity pricing"""
        # Perplexity charges per request
        # Assuming $0.005 per request for sonar-medium
        cost_per_request = 0.005
        return query_count * cost_per_request
```

**[SLIDE 13: Key Implementation Points]**

"Let me highlight the important parts:

1. **API Integration**: We use aiohttp for async HTTP calls
2. **Query Building**: We construct natural language queries that Perplexity understands
3. **Response Parsing**: We extract structured data from the LLM response
4. **Error Handling**: We gracefully handle parsing errors
5. **Cost Estimation**: We can predict costs before running searches

**[HANDS-ON EXERCISE]** "Your turn! Pause the video and implement a similar adapter for Tavily or another search API. Use the same pattern but adapt for their API structure."

## Section 7: Integrating Everything (10 minutes)

**[SLIDE 14: Using MCP Tools in Use Cases]**

"Now let's see how to use our MCP tools in the actual use case:

```python
# v2/src/core/use_cases/discover_similar_companies.py

class DiscoverSimilarCompaniesUseCase:
    def __init__(
        self,
        mcp_registry: MCPToolRegistry,
        aggregator: MCPResultAggregator,
        vector_store: VectorStore  # fallback
    ):
        self.mcp_registry = mcp_registry
        self.aggregator = aggregator
        self.vector_store = vector_store
    
    async def execute(
        self,
        company_name: str,
        use_tools: Optional[List[str]] = None,
        limit: int = 20
    ) -> SimilarityResult:
        
        # Determine which tools to use
        if use_tools:
            tools = [self.mcp_registry.get_tool(name) for name in use_tools]
        else:
            # Use all available tools
            tools = self.mcp_registry.get_all_tools()
        
        if not tools:
            # Fallback to vector search
            return await self._fallback_vector_search(company_name, limit)
        
        # Run searches in parallel
        results_by_tool = await self._search_with_all_tools(
            company_name, tools, limit
        )
        
        # Aggregate results
        aggregated_companies = self.aggregator.aggregate_results(results_by_tool)
        
        # Create result
        result = SimilarityResult(
            source_company_name=company_name,
            primary_method=SimilarityMethod.MCP_TOOL,
            similar_companies=aggregated_companies[:limit],
            total_found=len(aggregated_companies)
        )
        
        # Track which tools were used
        for tool in tools:
            result.mcp_tools_used.append(tool.get_tool_info())
        
        return result
    
    async def _search_with_all_tools(
        self,
        company_name: str,
        tools: List[MCPSearchTool],
        limit: int
    ) -> Dict[str, List[SimilarCompany]]:
        """Run searches with all tools in parallel"""
        
        import asyncio
        
        # Create tasks for parallel execution
        tasks = []
        tool_names = []
        
        for tool in tools:
            task = tool.search_similar_companies(company_name, limit=limit)
            tasks.append(task)
            tool_names.append(tool.get_tool_info().tool_name)
        
        # Run all searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        results_by_tool = {}
        for tool_name, result in zip(tool_names, results):
            if isinstance(result, Exception):
                print(f"⚠️ Tool {tool_name} failed: {result}")
                results_by_tool[tool_name] = []
            else:
                results_by_tool[tool_name] = result
        
        return results_by_tool
```

**[SLIDE 15: Configuration]**

"Let's see how users configure their MCP tools:

```python
# config/mcp_tools.yaml

mcp_tools:
  perplexity:
    enabled: true
    api_key: ${PERPLEXITY_API_KEY}
    config:
      model: "sonar-medium-online"
      search_recency: "week"
      temperature: 0.2
  
  tavily:
    enabled: true
    api_key: ${TAVILY_API_KEY}
    config:
      search_depth: "advanced"
      include_domains: ["techcrunch.com", "bloomberg.com"]
      max_results: 20
  
  custom_enterprise:
    enabled: false
    endpoint: "https://search.company.internal"
    auth_token: ${ENTERPRISE_SEARCH_TOKEN}

default_tools: ["perplexity", "tavily"]
fallback_to_vector_search: true
```

## Section 8: Testing MCP Tools (8 minutes)

**[SLIDE 16: Testing Strategy]**

"Testing is crucial. Let's write comprehensive tests:

```python
# v2/tests/integration/test_mcp_tools.py

import pytest
from unittest.mock import AsyncMock, MagicMock

class TestMCPIntegration:
    
    @pytest.fixture
    def mock_perplexity_tool(self):
        """Create a mock Perplexity tool for testing"""
        tool = AsyncMock(spec=PerplexitySearchTool)
        tool.get_tool_info.return_value = MCPToolInfo(
            tool_name="perplexity_search",
            tool_version="1.0",
            capabilities=["web_search"]
        )
        return tool
    
    @pytest.mark.asyncio
    async def test_mcp_registry(self):
        """Test tool registration and retrieval"""
        registry = MCPToolRegistry()
        
        # Create a mock tool
        tool = AsyncMock(spec=MCPSearchTool)
        tool.get_tool_info.return_value = MCPToolInfo(
            tool_name="test_tool",
            tool_version="1.0"
        )
        tool.validate_configuration.return_value = True
        
        # Register the tool
        registry.register_tool(tool)
        
        # Retrieve the tool
        retrieved = registry.get_tool("test_tool")
        assert retrieved == tool
        
        # Test non-existent tool
        with pytest.raises(KeyError):
            registry.get_tool("non_existent")
    
    @pytest.mark.asyncio
    async def test_result_aggregation(self):
        """Test aggregating results from multiple tools"""
        aggregator = MCPResultAggregator()
        
        # Create test data
        results_by_tool = {
            "tool1": [
                SimilarCompany(name="Stripe", website="stripe.com"),
                SimilarCompany(name="Square", website="squareup.com")
            ],
            "tool2": [
                SimilarCompany(name="Stripe", website="stripe.com"),  # Duplicate
                SimilarCompany(name="PayPal", website="paypal.com")
            ]
        }
        
        # Aggregate
        aggregated = aggregator.aggregate_results(results_by_tool)
        
        # Should have 3 companies (Stripe deduplicated)
        assert len(aggregated) == 3
        company_names = [c.name for c in aggregated]
        assert "Stripe" in company_names
        assert "Square" in company_names
        assert "PayPal" in company_names
    
    @pytest.mark.asyncio
    async def test_use_case_with_mcp_tools(self, mock_perplexity_tool):
        """Test the complete use case flow"""
        # Setup
        registry = MCPToolRegistry()
        registry._tools["perplexity_search"] = mock_perplexity_tool
        
        aggregator = MCPResultAggregator()
        vector_store = AsyncMock()
        
        use_case = DiscoverSimilarCompaniesUseCase(
            registry, aggregator, vector_store
        )
        
        # Configure mock to return companies
        mock_perplexity_tool.search_similar_companies.return_value = [
            SimilarCompany(
                name="Square",
                website="squareup.com",
                mcp_confidence=0.9
            )
        ]
        
        # Execute
        result = await use_case.execute(
            company_name="Stripe",
            use_tools=["perplexity_search"]
        )
        
        # Verify
        assert result.primary_method == SimilarityMethod.MCP_TOOL
        assert len(result.similar_companies) == 1
        assert result.similar_companies[0].name == "Square"
        assert len(result.mcp_tools_used) == 1
        assert result.mcp_tools_used[0].tool_name == "perplexity_search"
```

**[TESTING TIP]** "Always mock external API calls in unit tests. For integration tests, consider using a test API key with rate limits."

## Section 9: Production Considerations (5 minutes)

**[SLIDE 17: Production Checklist]**

"Before deploying to production, consider these important points:

### 1. **Rate Limiting**
```python
class RateLimitedMCPTool(MCPSearchTool):
    def __init__(self, tool: MCPSearchTool, requests_per_minute: int = 60):
        self.tool = tool
        self.rate_limiter = RateLimiter(requests_per_minute)
    
    async def search_similar_companies(self, *args, **kwargs):
        async with self.rate_limiter:
            return await self.tool.search_similar_companies(*args, **kwargs)
```

### 2. **Error Recovery**
```python
class ResilientMCPTool(MCPSearchTool):
    async def search_similar_companies(self, *args, **kwargs):
        for attempt in range(3):
            try:
                return await self.tool.search_similar_companies(*args, **kwargs)
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 3. **Cost Tracking**
```python
class CostTrackingMCPTool(MCPSearchTool):
    def __init__(self, tool: MCPSearchTool, cost_tracker: CostTracker):
        self.tool = tool
        self.cost_tracker = cost_tracker
    
    async def search_similar_companies(self, *args, **kwargs):
        estimated_cost = self.tool.estimate_cost(1)
        
        # Track before the request
        await self.cost_tracker.record_usage(
            tool_name=self.tool.get_tool_info().tool_name,
            estimated_cost=estimated_cost
        )
        
        return await self.tool.search_similar_companies(*args, **kwargs)
```

### 4. **Monitoring**
```python
# Add OpenTelemetry instrumentation
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class MonitoredMCPTool(MCPSearchTool):
    async def search_similar_companies(self, company_name: str, **kwargs):
        with tracer.start_as_current_span(
            "mcp_tool_search",
            attributes={
                "tool_name": self.get_tool_info().tool_name,
                "company_name": company_name
            }
        ) as span:
            start_time = time.time()
            try:
                results = await self.tool.search_similar_companies(company_name, **kwargs)
                span.set_attribute("result_count", len(results))
                return results
            except Exception as e:
                span.record_exception(e)
                raise
            finally:
                duration = time.time() - start_time
                span.set_attribute("duration_ms", duration * 1000)
```

## Conclusion (3 minutes)

**[SLIDE 18: What We Built]**

"Congratulations! You've built a production-ready MCP search plugin system. Let's recap what we accomplished:

✅ **Extensible Architecture**: Any MCP tool can be plugged in
✅ **Domain Model Support**: Clean separation of concerns
✅ **Parallel Execution**: Multiple tools search simultaneously  
✅ **Smart Aggregation**: Deduplication and confidence ranking
✅ **Production Ready**: Rate limiting, monitoring, and error handling

**[SLIDE 19: Next Steps]**

Your homework:
1. Implement a Tavily adapter using the same pattern
2. Add caching to reduce API costs
3. Build a custom MCP tool for your company's internal search
4. Create a UI for users to configure their MCP tools

**[FINAL THOUGHT]**
"Remember, the power of this architecture is that it grows with your needs. As new AI search tools emerge, you can add them without changing your core code. That's the beauty of clean architecture!

Thank you for joining me in this tutorial. If you have questions, leave them in the comments below. Happy coding!"

---

## Instructor Notes:
- Total runtime: ~60 minutes
- Include code repository link in video description
- Create downloadable PDF with all code snippets
- Consider follow-up video on building custom MCP tools
- Emphasize typing `async`/`await` correctly in live coding