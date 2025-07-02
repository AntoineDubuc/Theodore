# Theodore v2 Product Requirements Document (PRD)

## 1. Product Overview

### 1.1 Product Name
Theodore CLI - AI-Powered Company Intelligence Platform

### 1.2 Product Description
Theodore CLI is a command-line tool that leverages AI to gather, analyze, and provide actionable intelligence about companies. It serves as a foundational platform for sales teams, researchers, and developers to programmatically access company insights.

### 1.3 Problem Statement
Current company intelligence gathering is:
- Manual and time-consuming
- Fragmented across multiple tools
- Difficult to integrate into workflows
- Not scalable for large datasets
- Limited to web interfaces

### 1.4 Solution
A CLI-first platform that:
- Automates company research through AI
- Provides programmatic access to intelligence
- Enables batch processing and automation
- Supports custom extensions via plugins
- Integrates seamlessly into existing workflows

## 2. User Personas

### 2.1 Primary Persona: DevOps Engineer "Alex"
- **Role**: DevOps/Automation Engineer at sales organization
- **Goals**: Automate company research for sales team
- **Pain Points**: Manual processes, no API access, can't integrate with CRM
- **Needs**: CLI tools, scriptable interface, batch processing

### 2.2 Secondary Persona: Sales Operations Manager "Sarah"
- **Role**: Sales Ops Manager at B2B SaaS company
- **Goals**: Enrich CRM data with company intelligence
- **Pain Points**: Incomplete data, manual enrichment, no bulk operations
- **Needs**: Bulk processing, CSV import/export, scheduling

### 2.3 Tertiary Persona: Developer "Marcus"
- **Role**: Third-party developer/consultant
- **Goals**: Build custom integrations for clients
- **Pain Points**: No extensibility, closed systems
- **Needs**: Plugin API, documentation, examples

## 3. Functional Requirements

### 3.1 Core CLI Commands

#### 3.1.1 Company Research
```bash
theodore research <company-name> <website>
```
- **Priority**: P0 (Must Have)
- **Description**: Research a single company
- **Acceptance Criteria**:
  - Accepts company name and website
  - Returns structured JSON output
  - Supports output format flags (--json, --yaml, --table)
  - Shows real-time progress
  - Handles errors gracefully

#### 3.1.2 Bulk Research
```bash
theodore research-bulk <csv-file>
```
- **Priority**: P0
- **Description**: Research multiple companies from CSV
- **Acceptance Criteria**:
  - Processes CSV with name,website columns
  - Supports resume on failure
  - Progress tracking for each company
  - Outputs results to specified format
  - Rate limiting and retry logic

#### 3.1.3 Company Discovery
```bash
theodore discover <company-name> [--limit 10]
```
- **Priority**: P0
- **Description**: Find similar companies
- **Acceptance Criteria**:
  - Returns list of similar companies
  - Configurable result limit
  - Includes similarity scores
  - Supports filtering options

#### 3.1.4 Data Export
```bash
theodore export [--format csv|json|excel] [--filter <query>]
```
- **Priority**: P1 (Should Have)
- **Description**: Export company data
- **Acceptance Criteria**:
  - Multiple export formats
  - Query filtering support
  - Include/exclude fields option
  - Handles large datasets

#### 3.1.5 Plugin Management
```bash
theodore plugin install <plugin-name>
theodore plugin list
theodore plugin remove <plugin-name>
```
- **Priority**: P1
- **Description**: Manage plugins
- **Acceptance Criteria**:
  - Install from registry or GitHub
  - List installed plugins
  - Show plugin information
  - Handle dependencies

### 3.2 Configuration Management

#### 3.2.1 Global Configuration
```bash
theodore config set <key> <value>
theodore config get <key>
theodore config list
```
- **Priority**: P0
- **Description**: Manage configuration
- **Acceptance Criteria**:
  - Persistent configuration storage
  - Environment variable override
  - Secure credential storage
  - Configuration validation

### 3.3 Authentication & API Keys

#### 3.3.1 Credential Management
```bash
theodore auth login
theodore auth logout
theodore auth status
```
- **Priority**: P0
- **Description**: Manage authentication
- **Acceptance Criteria**:
  - Secure credential storage
  - Multiple auth methods
  - Token refresh handling
  - Clear error messages

## 4. Non-Functional Requirements

### 4.1 Performance
- Command response time: <100ms for non-processing commands
- Research processing: <30s per company (50% improvement over v1)
- Bulk processing: 100 companies/hour minimum
- Memory usage: <500MB for standard operations

### 4.2 Reliability
- 99.9% uptime for API services
- Automatic retry with exponential backoff
- Graceful degradation when services unavailable
- Data consistency guarantees

### 4.3 Security
- Encrypted credential storage
- API key rotation support
- Plugin sandboxing
- No sensitive data in logs

### 4.4 Usability
- Intuitive command structure
- Helpful error messages
- Built-in help system
- Progress indicators for long operations

### 4.5 Compatibility
- Python 3.8+ support
- Windows, macOS, Linux
- Docker container option
- Shell completion (bash, zsh, fish)

## 5. Technical Requirements

### 5.1 Architecture
- Hexagonal architecture (ports & adapters)
- Plugin system based on well-defined interfaces
- Event-driven internal communication
- Dependency injection for testability

### 5.2 Data Storage
- Local SQLite for cache
- Remote PostgreSQL for shared data
- S3-compatible storage for exports
- Redis for queue management

### 5.3 Integration Points
- REST API for UI attachment
- Webhook support for notifications
- CSV/JSON import/export
- CRM integrations via plugins

## 6. User Experience

### 6.1 Installation
```bash
# Via pip
pip install theodore-cli

# Via homebrew
brew install theodore

# Via docker
docker run theodore/cli
```

### 6.2 First Run Experience
```bash
$ theodore --help
Theodore CLI - AI Company Intelligence

Usage: theodore [OPTIONS] COMMAND [ARGS]...

Commands:
  research      Research a company
  discover      Find similar companies
  export        Export company data
  plugin        Manage plugins
  config        Manage configuration
  auth          Authentication commands

$ theodore auth login
Welcome to Theodore CLI!
Please enter your API key: ********
✓ Authentication successful!

$ theodore research "Acme Corp" "acme.com"
🔍 Researching Acme Corp...
✓ Phase 1: Link discovery (found 127 pages)
✓ Phase 2: Page selection (selected 25 pages)
✓ Phase 3: Content extraction (completed in 12.3s)
✓ Phase 4: AI analysis (completed in 8.7s)

Company: Acme Corp
Industry: Technology
Size: 1000-5000 employees
...
```

### 6.3 Error Handling
```bash
$ theodore research "Invalid Company"
❌ Error: Website URL is required
Usage: theodore research <company-name> <website>

$ theodore research "Acme" "not-a-url"
❌ Error: Invalid website URL format
Please provide a valid URL (e.g., https://example.com)
```

## 7. Success Metrics

### 7.1 Adoption Metrics
- Active users: 100+ within 3 months
- Daily active commands: 1000+
- Plugin installations: 500+

### 7.2 Performance Metrics
- Average research time: <30s
- API response time: <100ms p95
- Success rate: >95%

### 7.3 Quality Metrics
- Bug reports: <5 per month
- User satisfaction: >4.5/5
- Documentation completeness: 100%

## 8. Launch Strategy

### 8.1 Beta Launch (Week 11)
- 10 beta users
- Feature complete
- Known issues documented

### 8.2 General Availability (Week 12)
- Public announcement
- PyPI release
- Documentation site live
- Plugin SDK available

## 9. Future Considerations

### 9.1 Version 2.1 (3 months)
- Real-time monitoring dashboard
- Advanced query language
- Batch scheduling
- Team collaboration features

### 9.2 Version 3.0 (6 months)
- GraphQL API
- Streaming responses
- Multi-language support
- Enterprise features

## 10. Dependencies

### 10.1 External Services
- AI Providers (Bedrock, Gemini, OpenAI)
- Vector Database (Pinecone)
- Web Scraping (Crawl4AI)

### 10.2 Internal Dependencies
- Authentication service
- Data storage layer
- Queue management
- Plugin registry

## Appendix A: Command Reference

| Command | Description | Priority |
|---------|-------------|----------|
| `theodore research` | Research single company | P0 |
| `theodore research-bulk` | Bulk research from CSV | P0 |
| `theodore discover` | Find similar companies | P0 |
| `theodore export` | Export data | P1 |
| `theodore plugin install` | Install plugin | P1 |
| `theodore config set` | Set configuration | P0 |
| `theodore auth login` | Authenticate | P0 |

## Appendix B: Plugin Interface

```python
from theodore.plugins import Plugin

class MyPlugin(Plugin):
    name = "my-plugin"
    version = "1.0.0"
    
    def get_provided_interfaces(self):
        return {
            ScraperPort: MyCustomScraper,
            AIProviderPort: MyAIProvider
        }
```