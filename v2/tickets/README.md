# Theodore v2 Development Tickets

This folder contains development tickets for implementing Theodore v2 with a clean architecture, CLI-first approach, and MCP-first search architecture.

## Ticket Organization

Tickets are organized by development phase with MCP (Model Context Protocol) support introduced early for pluggable search capabilities:

### Phase 1: Foundation (Tickets 1-9)
- **TICKET-001**: Core Domain Models
- **TICKET-002**: CLI Application Skeleton  
- **TICKET-003**: Configuration Management System
- **TICKET-004**: Progress Tracking System
- **TICKET-005**: MCP Search Droid Support ⭐ NEW POSITION
- **TICKET-006**: Domain Discovery Adapter
- **TICKET-007**: Web Scraper Port Definition
- **TICKET-008**: AI Provider Port Definition
- **TICKET-009**: Vector Storage Port Definition

### Phase 2: Core Use Cases (Tickets 10-11)
- **TICKET-010**: Research Company Use Case
- **TICKET-011**: Discover Similar Companies Use Case (MCP-aware)

### Phase 3: Infrastructure Adapters (Tickets 12-18)
- **TICKET-012**: Google Search Adapter (Legacy fallback)
- **TICKET-013**: Crawl4AI Scraper Adapter
- **TICKET-014**: AWS Bedrock Adapter
- **TICKET-015**: Google Gemini Adapter
- **TICKET-016**: Pinecone Vector Storage Adapter
- **TICKET-017**: MCP Perplexity Adapter ⭐ NEW
- **TICKET-018**: MCP Tavily Adapter ⭐ NEW

### Phase 4: Integration (Tickets 19-22)
- **TICKET-019**: Dependency Injection Container
- **TICKET-020**: CLI Research Command Implementation
- **TICKET-021**: CLI Discover Command Implementation (MCP-enabled)
- **TICKET-022**: Batch Processing System

### Phase 5: Advanced Features (Tickets 23-27)
- **TICKET-023**: Plugin System Foundation
- **TICKET-024**: REST API Server
- **TICKET-025**: Export Functionality
- **TICKET-026**: Logging and Monitoring
- **TICKET-027**: End-to-End Integration Tests

## Key Architecture Changes

### MCP-First Search Architecture
Theodore v2 prioritizes pluggable MCP search tools over hardcoded search implementations:

1. **Early MCP Support** (Ticket 5): Establishes the foundation for pluggable search tools
2. **MCP Tool Registry**: Manages available search droids and their configurations
3. **Standard Interface**: All search tools implement the same port interface
4. **Parallel Execution**: Multiple MCP tools can search simultaneously
5. **Result Aggregation**: Intelligent deduplication and confidence scoring
6. **Legacy Fallback**: Google Search remains available when no MCP tools are configured

### Benefits of MCP-First Approach
- **Extensibility**: Easy to add new search tools without changing core logic
- **User Choice**: Users can configure their preferred search providers
- **Performance**: Parallel search across multiple tools
- **Cost Control**: Users manage their own API keys and costs
- **Future-Proof**: Ready for new AI search tools as they emerge

## Development Approach

Each ticket is designed to be:
1. **Small and focused** - Can be completed in 2-8 hours
2. **Independently testable** - Has clear acceptance criteria
3. **Value-delivering** - Provides working functionality
4. **Well-defined** - Includes technical details and testing requirements

## Testing Strategy

Every ticket includes:
- Unit tests for business logic
- Integration tests with real services where applicable
- Example commands or code for manual testing
- Real company data for validation

## Getting Started

1. Start with Phase 1 tickets to establish the foundation
2. **Ticket 5 (MCP Support) is critical** - implement early to enable pluggable search
3. Phase 2 use cases will leverage MCP tools for discovery
4. Phase 3 can develop adapters in parallel
5. Each ticket lists its dependencies explicitly

## For Claude Code

When implementing a ticket:
1. Read the acceptance criteria carefully
2. Follow the technical details section
3. Create all files listed in "Files to Create"
4. Write tests first (TDD) when possible
5. Test with the real data examples provided
6. Ensure the implementation matches v1 functionality where applicable
7. For MCP adapters, follow the established port interface pattern