# TICKET-020: CLI Research Command Implementation

## Overview
Implement the comprehensive `theodore research` command that provides a beautiful, user-friendly interface to Theodore v2's company intelligence capabilities with real-time progress tracking and multiple output formats.

## Problem Statement
Users need an intuitive command-line interface to research companies that:
- Provides immediate feedback during long-running AI operations
- Presents results in multiple formats for different use cases
- Handles errors gracefully with actionable error messages
- Supports both guided research (with website) and discovery research (company name only)
- Integrates seamlessly with Theodore's dependency injection container
- Maintains professional CLI UX standards with Rich formatting

Without a well-designed CLI research command, users cannot effectively access Theodore's powerful AI-driven company intelligence capabilities.

## Acceptance Criteria
- [ ] Parse company name and optional website with comprehensive validation
- [ ] Show real-time progress during all research phases with Rich progress bars
- [ ] Display beautifully formatted results with multiple output options
- [ ] Support output formats: table (default), json, yaml, markdown
- [ ] Handle errors gracefully with helpful suggestions and troubleshooting
- [ ] Support --no-domain-discovery flag for faster research
- [ ] Provide --verbose flag for detailed operation logs
- [ ] Support --timeout flag for custom operation timeouts
- [ ] Implement --save flag to store results to file
- [ ] Handle Ctrl+C gracefully with proper cleanup
- [ ] Integrate with DI container for proper dependency management
- [ ] Support configuration overrides via CLI flags
- [ ] Provide comprehensive help documentation and examples

## Technical Details

### CLI Architecture Integration
The research command integrates with Theodore's layered architecture:

```
CLI Layer (research.py)
├── Argument Parsing (Click framework)
├── Progress Display (Rich live display)
├── DI Container Integration (TICKET-019)
├── Use Case Orchestration (ResearchCompany)
├── Output Formatting (Multiple formats)
└── Error Handling (User-friendly messages)
```

### Command Signature and Options
```bash
theodore research [OPTIONS] COMPANY_NAME [WEBSITE]

Options:
  --output, -o [table|json|yaml|markdown]  Output format [default: table]
  --no-domain-discovery                    Skip automatic domain discovery
  --verbose, -v                           Enable verbose logging
  --timeout INTEGER                       Timeout in seconds [default: 60]
  --save PATH                            Save results to file
  --config-override TEXT                 Override configuration (key=value)
  --help                                 Show this message and exit

Examples:
  theodore research "Apple Inc" "apple.com"
  theodore research "Salesforce" --output json --save results.json
  theodore research "Unknown Startup" --no-domain-discovery --verbose
```

### Dependency Injection Integration
Must properly integrate with ApplicationContainer from TICKET-019:

```python
# Container resolution pattern
container = ContainerFactory.create_cli_container()
research_use_case = container.use_cases.research_company()

# Progress callback injection
def progress_callback(phase: str, progress: float, message: str):
    live_display.update_progress(phase, progress, message)

research_use_case.set_progress_callback(progress_callback)
```

### Real-Time Progress Display System
Comprehensive progress tracking across all research phases:

1. **Domain Discovery Phase** (if enabled)
   - Website validation and domain resolution
   - Progress: 0-20%

2. **AI Research Phase**
   - MCP search tool execution
   - LLM intelligence generation
   - Progress: 20-70%

3. **Similarity Analysis Phase**
   - Vector embedding generation
   - Similarity search execution
   - Progress: 70-90%

4. **Results Compilation Phase**
   - Data aggregation and formatting
   - Final validation
   - Progress: 90-100%

### Output Formatting Strategy
Support multiple output formats for different use cases:

**Table Format (Default):**
- Beautiful Rich tables with color coding
- Hierarchical display for nested data
- Optimized for terminal viewing
- Smart column width adjustment

**JSON Format:**
- Machine-readable structured data
- Preserves all data relationships
- Suitable for API integration
- Pretty-printed with indentation

**YAML Format:**
- Human-readable structured data
- Good for configuration files
- Preserves comments and metadata
- Clean hierarchical display

**Markdown Format:**
- Documentation-ready output
- Tables and structured sections
- Perfect for reports and sharing
- GitHub-compatible formatting

### Error Handling and User Experience
Comprehensive error handling with actionable guidance:

**Network Errors:**
- Clear messages about connectivity issues
- Suggestions for proxy configuration
- Retry mechanisms with exponential backoff

**API Errors:**
- API key validation and helpful setup instructions
- Rate limit handling with wait time estimates
- Service availability checks with alternatives

**Input Validation Errors:**
- Company name format validation
- Website URL validation and correction suggestions
- Configuration parameter validation

**Timeout Handling:**
- Graceful cancellation of in-progress operations
- Partial results display when possible
- Resume capability for long operations

### File Structure
Create comprehensive CLI research system:

```
v2/src/cli/
├── commands/
│   └── research.py              # Main research command implementation
├── formatters/
│   ├── __init__.py             # Formatter registry and exports
│   ├── base.py                 # Base formatter interface
│   ├── company.py              # Company data formatting logic
│   ├── table.py                # Rich table formatting
│   ├── json_formatter.py       # JSON output formatting
│   ├── yaml_formatter.py       # YAML output formatting
│   └── markdown_formatter.py   # Markdown output formatting
├── progress/
│   ├── __init__.py             # Progress display exports
│   ├── live_display.py         # Rich live progress display
│   ├── progress_tracker.py     # Progress state management
│   └── phase_manager.py        # Research phase coordination
└── utils/
    ├── validation.py           # Input validation utilities
    ├── error_handling.py       # Error message formatting
    └── file_operations.py      # File save/load operations
```

### Configuration Integration
Seamless integration with Theodore's configuration system:

```python
# CLI-specific configuration overrides
cli_config_overrides = {
    "timeout_seconds": timeout,
    "verbose_logging": verbose,
    "progress_display": True,
    "output_format": output_format
}

container.config.override(cli_config_overrides)
```

### Performance Considerations
- Async operation support for non-blocking UI updates
- Efficient memory usage for large result sets
- Smart caching for repeated operations
- Progress update throttling to prevent UI flickering

### Accessibility and Usability
- Color-blind friendly color schemes
- Screen reader compatible output
- Keyboard interrupt handling
- Clear progress indicators
- Helpful error messages with next steps

## Implementation Considerations

### Rich Integration Patterns
- Live display for real-time progress updates
- Styled text for different message types
- Progress bars with phase descriptions
- Tables with automatic column sizing
- Status indicators with color coding

### Error Recovery Strategies
- Automatic retry for transient failures
- Fallback to alternative search providers
- Partial result display on timeout
- Configuration validation before execution

### Testing Strategy
- Mock container integration for unit tests
- Progress callback testing with simulated delays
- Output format validation across all supported types
- Error scenario testing with realistic failure modes
- End-to-end testing with real command execution

### CLI Best Practices
- Consistent argument naming across commands
- Progressive disclosure of advanced options
- Helpful examples in command help
- Clear success/failure indicators
- Professional terminal output styling

## Files to Create

### Core Command Implementation (1 file)
1. **`v2/src/cli/commands/research.py`**
   - Main Click command implementation with comprehensive argument parsing
   - DI container integration with proper error handling
   - Progress callback setup and coordination
   - Output format routing and file saving
   - Graceful shutdown and cleanup handling
   - Configuration override support
   - Help documentation with examples

### Formatting System (6 files)
2. **`v2/src/cli/formatters/__init__.py`**
   - FormatterRegistry for dynamic format selection
   - Output format enumeration and validation
   - Factory pattern for formatter creation
   - Common formatting utilities and exports

3. **`v2/src/cli/formatters/base.py`**
   - BaseFormatter abstract class defining format interface
   - Common formatting methods and utilities
   - Data validation and transformation logic
   - Error handling for formatting operations

4. **`v2/src/cli/formatters/company.py`**
   - CompanyDataFormatter for business intelligence data
   - Structured display of company information
   - Similarity results formatting
   - Data hierarchical organization

5. **`v2/src/cli/formatters/table.py`**
   - RichTableFormatter using Rich tables
   - Dynamic column sizing and styling
   - Color-coded data representation
   - Nested table support for complex data

6. **`v2/src/cli/formatters/json_formatter.py`**
   - JSONFormatter with pretty-printing
   - Data serialization with custom encoders
   - Metadata preservation and structure
   - Validation of JSON output integrity

7. **`v2/src/cli/formatters/yaml_formatter.py`**
   - YAMLFormatter with clean output
   - Comment preservation and metadata
   - Hierarchical structure optimization
   - Custom YAML serializers for complex objects

8. **`v2/src/cli/formatters/markdown_formatter.py`**
   - MarkdownFormatter for documentation output
   - Table and section generation
   - GitHub-compatible formatting
   - Link generation and structure optimization

### Progress Display System (3 files)
9. **`v2/src/cli/progress/live_display.py`**
   - RichLiveDisplay for real-time progress updates
   - Multi-phase progress bar management
   - Status message display and styling
   - Performance optimized update throttling

10. **`v2/src/cli/progress/progress_tracker.py`**
    - ProgressTracker for state management
    - Phase transition handling
    - Progress calculation and normalization
    - Event logging and debugging support

11. **`v2/src/cli/progress/phase_manager.py`**
    - ResearchPhaseManager coordinating all phases
    - Phase-specific progress weighting
    - Error recovery and phase skipping
    - Timing and performance metrics

### Utility Support (3 files)
12. **`v2/src/cli/utils/validation.py`**
    - InputValidator for company names and URLs
    - Configuration parameter validation
    - Data sanitization and normalization
    - Error message generation with suggestions

13. **`v2/src/cli/utils/error_handling.py`**
    - CLIErrorHandler for user-friendly error messages
    - Error categorization and suggested actions
    - Debug information formatting
    - Recovery step generation

14. **`v2/src/cli/utils/file_operations.py`**
    - FileOperationManager for save/load operations
    - Format-specific file writing
    - File path validation and creation
    - Backup and recovery mechanisms

### Testing Implementation (2 files)
15. **`v2/tests/unit/cli/test_research_command.py`**
    - Comprehensive unit tests for research command
    - Mock container integration testing
    - Progress callback validation
    - Output format testing
    - Error handling scenario testing
    - Configuration override testing

16. **`v2/tests/e2e/test_research_cli.py`**
    - End-to-end CLI testing with real command execution
    - Integration testing with container
    - File output validation
    - Performance benchmarking
    - User experience validation

## Testing Strategy

### Unit Testing Approach
- Mock all external dependencies (container, use cases)
- Test argument parsing and validation
- Verify progress callback integration
- Validate output formatting across all formats
- Test error handling scenarios

### Integration Testing Approach
- Test with real container integration
- Validate progress display updates
- Test file save/load operations
- Verify configuration override behavior
- Test timeout and cancellation handling

### End-to-End Testing Approach
- Full command execution testing
- Real use case integration
- Performance and timing validation
- User experience testing
- Cross-platform compatibility testing

### Test Scenarios
```python
def test_research_command_with_website():
    """Test research command with explicit website"""
    
def test_research_command_discovery_mode():
    """Test research without website (discovery mode)"""
    
def test_output_format_json():
    """Test JSON output format generation"""
    
def test_progress_display_updates():
    """Test real-time progress display"""
    
def test_error_handling_network_failure():
    """Test graceful network error handling"""
    
def test_ctrl_c_handling():
    """Test graceful Ctrl+C shutdown"""
    
def test_file_save_operations():
    """Test saving results to various formats"""
    
def test_configuration_overrides():
    """Test CLI configuration parameter overrides"""
```

## Estimated Time: 5-6 hours

## Dependencies
- TICKET-010 (ResearchCompany use case for business logic)
- TICKET-019 (DI container for component wiring)
- TICKET-002 (CLI skeleton for basic structure)
- TICKET-003 (Configuration system for settings)

## CLI Usage Examples

### Basic Research Operations
```bash
# Research with explicit website
theodore research "Salesforce" "salesforce.com"

# Research with domain discovery
theodore research "Apple Inc"

# Fast research without domain discovery
theodore research "Microsoft" --no-domain-discovery
```

### Output Format Options
```bash
# JSON output for API integration
theodore research "Google" --output json

# YAML output for configuration
theodore research "Amazon" --output yaml

# Markdown output for documentation
theodore research "Tesla" --output markdown

# Default table output
theodore research "Netflix"
```

### Advanced Usage
```bash
# Save results to file
theodore research "Stripe" --output json --save stripe-research.json

# Verbose logging for debugging
theodore research "Unknown Company" --verbose

# Custom timeout for complex research
theodore research "Complex Enterprise" --timeout 300

# Configuration overrides
theodore research "TestCorp" --config-override "ai_provider=bedrock"
```

### Error Handling Examples
```bash
# Network connectivity issues
$ theodore research "Example Corp"
Error: Network connectivity failed
Suggestions:
  - Check internet connection
  - Verify proxy settings in config
  - Try again with --timeout 120

# Missing API keys
$ theodore research "Test Company"
Error: OpenAI API key not configured
Suggestions:
  - Set OPENAI_API_KEY environment variable
  - Run: export OPENAI_API_KEY=your-key-here
  - Check configuration with: theodore config show
```

---

## Udemy Tutorial: Building a Production-Grade CLI Research Command

### Introduction (8 minutes)

Welcome to this comprehensive tutorial on building a professional command-line interface for Theodore v2's company research capabilities. We're going to create a CLI command that not only delivers powerful AI-driven company intelligence but does so with the polish and user experience you'd expect from world-class developer tools.

In this tutorial, we'll build the `theodore research` command that seamlessly integrates with our dependency injection container, provides real-time progress feedback during long-running AI operations, and presents results in multiple beautiful formats. This isn't just about connecting a few functions together - we're creating a production-ready CLI that handles errors gracefully, provides helpful guidance, and maintains professional standards throughout.

**Why is this tutorial critical for Theodore v2?** Because the CLI is often the first impression users have of our AI system. A well-designed command-line interface can make the difference between users embracing Theodore's capabilities or abandoning it in frustration. We'll see how thoughtful UX design, comprehensive error handling, and beautiful output formatting combine to create a tool that users genuinely enjoy using.

**What makes this CLI implementation special?** We're building more than just a command parser. Our implementation features:
- Real-time progress tracking with Rich progress bars that show exactly what's happening during AI operations
- Multiple output formats (table, JSON, YAML, markdown) optimized for different use cases
- Intelligent error handling that doesn't just tell users what went wrong, but suggests specific actions to fix problems
- Seamless integration with our dependency injection container for clean, testable code
- Professional-grade input validation and graceful shutdown handling

By the end of this tutorial, you'll understand how to build CLI interfaces that rival the best developer tools in terms of user experience, reliability, and maintainability.

Let's start by exploring the architecture and understanding how our CLI command fits into Theodore's broader system design.

### CLI Architecture and Design Philosophy (10 minutes)

Before we dive into implementation, let's understand the architectural principles that guide our CLI design and how it integrates with Theodore v2's hexagonal architecture.

**The CLI Layer's Role in Hexagonal Architecture**
Our CLI command serves as an adapter in the ports and adapters pattern, translating user intentions into domain operations:

```
User Input → CLI Adapter → Application Use Cases → Domain Logic → Infrastructure Adapters
```

The beauty of this approach is that our CLI remains completely decoupled from business logic. The ResearchCompany use case doesn't know or care whether it's being called from a CLI, web API, or scheduled job. This separation makes our code highly testable and enables us to evolve the user interface independently of the core functionality.

**Progressive Enhancement Philosophy**
Our CLI follows a progressive enhancement approach where basic functionality works immediately, but advanced features provide additional value:

Level 1: Basic research with simple output
Level 2: Real-time progress and formatted tables  
Level 3: Multiple output formats and file saving
Level 4: Advanced configuration and error recovery

This ensures that new users can get value immediately while power users can access sophisticated features.

**Rich Integration for Professional UX**
We're using the Rich library not just for pretty colors, but to create genuinely helpful user experiences:
- Progress bars that show current operation and time estimates
- Tables that automatically adjust to terminal width
- Color coding that provides semantic meaning (green for success, yellow for warnings)
- Live displays that update in real-time without screen flicker

**Error Handling Philosophy: Guide, Don't Punish**
When things go wrong, our CLI doesn't just report errors - it guides users toward solutions:

Instead of: "Error: API key not found"
We provide: "OpenAI API key not configured. Set it with: export OPENAI_API_KEY=your-key"

This approach transforms error messages from frustrating roadblocks into helpful guidance.

**Dependency Injection Integration Strategy**
Our CLI command integrates cleanly with the ApplicationContainer we built in TICKET-019:

```python
# Container setup with CLI-specific optimizations
container = ContainerFactory.create_cli_container()

# Use case resolution with progress callback injection
research_use_case = container.use_cases.research_company()
research_use_case.set_progress_callback(self.update_progress)
```

This integration gives us access to the full power of Theodore's AI capabilities while maintaining clean separation of concerns.

**Output Format Strategy**
Different users need different output formats for different purposes:
- **Table**: Human reading and terminal display
- **JSON**: API integration and programmatic processing  
- **YAML**: Configuration files and human-readable structured data
- **Markdown**: Documentation and sharing

Each format is optimized for its specific use case while preserving all the underlying data.

Let's see how these principles translate into actual code implementation.

### Implementing the Core Research Command (12 minutes)

Let's build the heart of our CLI research command - the main function that orchestrates the entire research process with beautiful progress tracking and comprehensive error handling.

```python
# v2/src/cli/commands/research.py
import click
import asyncio
from typing import Optional, Dict, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
import logging

from ...infrastructure.container import ContainerFactory
from ...application.use_cases.research_company import ResearchCompanyUseCase
from ..formatters import FormatterRegistry
from ..progress import ResearchProgressTracker
from ..utils.validation import InputValidator
from ..utils.error_handling import CLIErrorHandler
from ..utils.file_operations import FileOperationManager

logger = logging.getLogger(__name__)
console = Console()

@click.command()
@click.argument('company_name', type=str)
@click.argument('website', type=str, required=False)
@click.option('--output', '-o', 
              type=click.Choice(['table', 'json', 'yaml', 'markdown']),
              default='table',
              help='Output format for results')
@click.option('--no-domain-discovery', 
              is_flag=True,
              help='Skip automatic domain discovery for faster research')
@click.option('--verbose', '-v',
              is_flag=True, 
              help='Enable verbose logging and detailed progress')
@click.option('--timeout',
              type=int,
              default=60,
              help='Timeout for research operation in seconds')
@click.option('--save',
              type=click.Path(),
              help='Save results to specified file path')
@click.option('--config-override',
              multiple=True,
              help='Override configuration (format: key=value)')
@click.pass_context
async def research(
    ctx: click.Context,
    company_name: str,
    website: Optional[str],
    output: str,
    no_domain_discovery: bool,
    verbose: bool,
    timeout: int,
    save: Optional[str],
    config_override: tuple
):
    """
    Research a company using AI-powered intelligence gathering.
    
    Performs comprehensive company analysis including business intelligence,
    competitor analysis, and similarity scoring using advanced AI models.
    
    Examples:
        theodore research "Salesforce" "salesforce.com"
        theodore research "Apple Inc" --output json --save apple-research.json
        theodore research "Unknown Startup" --no-domain-discovery --verbose
    """
    
    error_handler = CLIErrorHandler(console, verbose)
    
    try:
        # Phase 1: Input validation and setup
        await _setup_and_validate_inputs(
            company_name, website, output, timeout, config_override, error_handler
        )
        
        # Phase 2: Container initialization with CLI optimizations
        container = await _initialize_container(config_override, verbose, timeout)
        
        # Phase 3: Progress tracking setup
        progress_tracker = ResearchProgressTracker(console, verbose)
        
        # Phase 4: Execute research with live progress display
        results = await _execute_research_with_progress(
            container, company_name, website, no_domain_discovery, 
            timeout, progress_tracker
        )
        
        # Phase 5: Format and display results
        await _format_and_display_results(
            results, output, save, progress_tracker
        )
        
        # Success indication
        console.print("✅ Research completed successfully!", style="bold green")
        
    except KeyboardInterrupt:
        await _handle_graceful_shutdown(progress_tracker)
    except Exception as e:
        await error_handler.handle_error(e, ctx)
        raise click.Abort()

async def _setup_and_validate_inputs(
    company_name: str,
    website: Optional[str], 
    output: str,
    timeout: int,
    config_override: tuple,
    error_handler: CLIErrorHandler
):
    """Validate all inputs and provide helpful error messages."""
    
    validator = InputValidator()
    
    # Validate company name
    if not validator.validate_company_name(company_name):
        error_handler.suggest_company_name_format(company_name)
        raise click.BadParameter("Invalid company name format")
    
    # Validate website if provided
    if website and not validator.validate_website_url(website):
        corrected_url = validator.suggest_url_correction(website)
        error_handler.suggest_website_correction(website, corrected_url)
        raise click.BadParameter(f"Invalid website URL: {website}")
    
    # Validate timeout
    if timeout < 10 or timeout > 600:
        raise click.BadParameter("Timeout must be between 10 and 600 seconds")
    
    # Validate configuration overrides
    for override in config_override:
        if '=' not in override:
            raise click.BadParameter(f"Invalid config override format: {override}")
            
    console.print(f"🔍 Researching: [bold cyan]{company_name}[/bold cyan]")
    if website:
        console.print(f"🌐 Website: [dim]{website}[/dim]")
```

**Container Integration with CLI Optimizations:**
```python
async def _initialize_container(
    config_overrides: tuple,
    verbose: bool,
    timeout: int
) -> ApplicationContainer:
    """Initialize DI container with CLI-specific optimizations."""
    
    try:
        # Create CLI-optimized container
        container = ContainerFactory.create_cli_container()
        
        # Apply CLI-specific configuration overrides
        cli_config = {
            "cli": {
                "verbose_logging": verbose,
                "progress_display": True,
                "default_timeout": timeout,
                "interactive_mode": True
            }
        }
        
        # Apply user configuration overrides
        user_overrides = {}
        for override in config_overrides:
            key, value = override.split('=', 1)
            user_overrides[key] = value
            
        container.config.override({**cli_config, **user_overrides})
        
        # Initialize container with progress indication
        with console.status("[bold blue]Initializing Theodore components..."):
            await container.initialize()
            
        console.print("✅ Container initialized successfully", style="dim green")
        return container
        
    except Exception as e:
        console.print(f"❌ Container initialization failed: {e}", style="bold red")
        raise
```

**Research Execution with Live Progress:**
```python
async def _execute_research_with_progress(
    container: ApplicationContainer,
    company_name: str,
    website: Optional[str],
    no_domain_discovery: bool,
    timeout: int,
    progress_tracker: ResearchProgressTracker
) -> Dict[str, Any]:
    """Execute research with comprehensive progress tracking."""
    
    # Get research use case from container
    research_use_case = container.use_cases.research_company()
    
    # Setup progress callback
    def progress_callback(phase: str, progress: float, message: str):
        progress_tracker.update_phase(phase, progress, message)
    
    research_use_case.set_progress_callback(progress_callback)
    
    # Create research parameters
    research_params = {
        "company_name": company_name,
        "website": website,
        "skip_domain_discovery": no_domain_discovery,
        "timeout_seconds": timeout
    }
    
    # Execute research with live progress display
    with progress_tracker.live_display() as live:
        try:
            progress_tracker.start_research()
            
            # Execute the actual research
            results = await asyncio.wait_for(
                research_use_case.execute(**research_params),
                timeout=timeout
            )
            
            progress_tracker.complete_research()
            return results
            
        except asyncio.TimeoutError:
            progress_tracker.timeout_research()
            console.print(f"⏰ Research timed out after {timeout} seconds", style="bold yellow")
            console.print("Try increasing timeout with --timeout flag or use --no-domain-discovery")
            raise
            
        except Exception as e:
            progress_tracker.error_research(str(e))
            raise
```

**Graceful Shutdown Handling:**
```python
async def _handle_graceful_shutdown(progress_tracker: ResearchProgressTracker):
    """Handle Ctrl+C gracefully with proper cleanup."""
    
    console.print("\n🛑 Research interrupted by user", style="bold yellow")
    
    # Give user option to save partial results
    if progress_tracker.has_partial_results():
        console.print("💾 Partial results available...")
        # Implementation for saving partial results
        
    console.print("👋 Goodbye!")
```

This implementation provides a robust foundation that handles errors gracefully, provides excellent user feedback, and integrates cleanly with our dependency injection system.

### Building the Progress Display System (10 minutes)

Let's create a sophisticated progress display system that provides real-time feedback during Theodore's AI operations, making long-running processes feel responsive and informative.

```python
# v2/src/cli/progress/progress_tracker.py
from typing import Optional, Dict, Any, Callable
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import time
from enum import Enum
from dataclasses import dataclass

class ResearchPhase(Enum):
    INITIALIZATION = "initialization"
    DOMAIN_DISCOVERY = "domain_discovery"  
    AI_RESEARCH = "ai_research"
    SIMILARITY_ANALYSIS = "similarity_analysis"
    RESULTS_COMPILATION = "results_compilation"
    COMPLETED = "completed"

@dataclass
class PhaseProgress:
    phase: ResearchPhase
    progress: float  # 0.0 to 1.0
    message: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None

class ResearchProgressTracker:
    """
    Comprehensive progress tracking for company research operations.
    
    Provides real-time visual feedback with Rich progress bars,
    phase-specific status updates, and timing information.
    """
    
    def __init__(self, console: Console, verbose: bool = False):
        self.console = console
        self.verbose = verbose
        self.phases: Dict[ResearchPhase, PhaseProgress] = {}
        self.current_phase: Optional[ResearchPhase] = None
        self.overall_start_time: Optional[float] = None
        self.partial_results: Dict[str, Any] = {}
        
        # Phase weight distribution for overall progress calculation
        self.phase_weights = {
            ResearchPhase.INITIALIZATION: 0.05,      # 5%
            ResearchPhase.DOMAIN_DISCOVERY: 0.15,    # 15%
            ResearchPhase.AI_RESEARCH: 0.50,         # 50%
            ResearchPhase.SIMILARITY_ANALYSIS: 0.25, # 25%
            ResearchPhase.RESULTS_COMPILATION: 0.05  # 5%
        }
        
        # Initialize progress tracking
        self._setup_progress_display()
        
    def _setup_progress_display(self):
        """Setup Rich progress bars and display components."""
        
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            MofNCompleteColumn(),
            TextColumn("[dim]{task.fields[message]}"),
            TimeElapsedColumn(),
            console=self.console,
            transient=False  # Keep completed bars visible
        )
        
        # Create tasks for each research phase
        self.phase_tasks = {}
        for phase in ResearchPhase:
            if phase != ResearchPhase.COMPLETED:
                task_id = self.progress.add_task(
                    description=self._get_phase_description(phase),
                    total=100,
                    message="Waiting...",
                    visible=False
                )
                self.phase_tasks[phase] = task_id
                
        # Overall progress task
        self.overall_task = self.progress.add_task(
            description="[bold]Overall Research Progress",
            total=100,
            message="Starting research...",
            visible=True
        )
        
    def _get_phase_description(self, phase: ResearchPhase) -> str:
        """Get human-readable description for each phase."""
        
        descriptions = {
            ResearchPhase.INITIALIZATION: "🚀 Initializing Research",
            ResearchPhase.DOMAIN_DISCOVERY: "🔍 Discovering Domain",
            ResearchPhase.AI_RESEARCH: "🤖 AI Intelligence Gathering", 
            ResearchPhase.SIMILARITY_ANALYSIS: "📊 Similarity Analysis",
            ResearchPhase.RESULTS_COMPILATION: "📋 Compiling Results"
        }
        return descriptions.get(phase, str(phase))
```

**Live Display Integration:**
```python
def live_display(self):
    """Create live display context manager for real-time updates."""
    
    return Live(
        self._generate_display_content(),
        console=self.console,
        refresh_per_second=4,  # Smooth but not overwhelming
        transient=False
    )
    
def _generate_display_content(self):
    """Generate the complete display content for live updates."""
    
    # Create main progress panel
    progress_panel = Panel(
        self.progress,
        title="[bold cyan]Theodore Company Research",
        border_style="blue",
        padding=(0, 1)
    )
    
    # Add phase details if verbose mode
    if self.verbose and self.current_phase:
        phase_info = self._generate_phase_info_table()
        return Group(progress_panel, phase_info)
    
    return progress_panel
    
def _generate_phase_info_table(self) -> Table:
    """Generate detailed phase information table for verbose mode."""
    
    table = Table(title="Research Phase Details", show_header=True)
    table.add_column("Phase", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Duration", justify="right")
    table.add_column("Details", style="dim")
    
    for phase, progress_info in self.phases.items():
        status_icon = "✅" if progress_info.end_time else "🔄" if progress_info.start_time else "⏳"
        
        duration = ""
        if progress_info.start_time:
            end_time = progress_info.end_time or time.time()
            duration = f"{end_time - progress_info.start_time:.1f}s"
            
        table.add_row(
            self._get_phase_description(phase),
            status_icon,
            duration,
            progress_info.message[:50] + "..." if len(progress_info.message) > 50 else progress_info.message
        )
        
    return table

def update_phase(self, phase_name: str, progress: float, message: str):
    """Update progress for a specific research phase."""
    
    try:
        phase = ResearchPhase(phase_name)
    except ValueError:
        # Handle unknown phase names gracefully
        if self.verbose:
            self.console.print(f"Unknown phase: {phase_name}", style="dim yellow")
        return
        
    # Initialize phase if not exists
    if phase not in self.phases:
        self.phases[phase] = PhaseProgress(
            phase=phase,
            progress=0.0,
            message="Starting...",
            start_time=time.time()
        )
        
        # Make phase task visible
        if phase in self.phase_tasks:
            self.progress.update(self.phase_tasks[phase], visible=True)
            
    # Update phase progress
    phase_progress = self.phases[phase]
    phase_progress.progress = max(0.0, min(1.0, progress))  # Clamp to valid range
    phase_progress.message = message
    
    # Update current phase tracking
    if progress > 0 and not phase_progress.start_time:
        phase_progress.start_time = time.time()
        
    if progress >= 1.0 and not phase_progress.end_time:
        phase_progress.end_time = time.time()
        
    self.current_phase = phase
    
    # Update Rich progress bars
    if phase in self.phase_tasks:
        self.progress.update(
            self.phase_tasks[phase],
            completed=int(progress * 100),
            message=message
        )
        
    # Update overall progress
    self._update_overall_progress()
    
def _update_overall_progress(self):
    """Calculate and update overall research progress."""
    
    total_weighted_progress = 0.0
    
    for phase, weight in self.phase_weights.items():
        if phase in self.phases:
            phase_progress = self.phases[phase].progress
            total_weighted_progress += phase_progress * weight
            
    overall_progress = min(100, int(total_weighted_progress * 100))
    
    # Generate overall status message
    if self.current_phase:
        current_message = self.phases[self.current_phase].message
        overall_message = f"{self._get_phase_description(self.current_phase)}: {current_message}"
    else:
        overall_message = "Preparing research..."
        
    self.progress.update(
        self.overall_task,
        completed=overall_progress,
        message=overall_message
    )
```

**Research State Management:**
```python
def start_research(self):
    """Initialize research tracking."""
    
    self.overall_start_time = time.time()
    self.console.print("🎯 Starting company research...", style="bold blue")
    
def complete_research(self):
    """Mark research as completed successfully."""
    
    if self.overall_start_time:
        total_time = time.time() - self.overall_start_time
        self.console.print(f"⏱️  Research completed in {total_time:.1f} seconds", style="bold green")
        
    # Complete all progress bars
    for task_id in self.phase_tasks.values():
        self.progress.update(task_id, completed=100, visible=True)
        
    self.progress.update(self.overall_task, completed=100, message="Research completed successfully!")
    
def timeout_research(self):
    """Handle research timeout scenario."""
    
    self.console.print("⏰ Research operation timed out", style="bold yellow")
    
    # Show which phases completed
    completed_phases = [
        phase for phase, progress in self.phases.items() 
        if progress.end_time is not None
    ]
    
    if completed_phases:
        self.console.print(f"✅ Completed phases: {', '.join([p.value for p in completed_phases])}", style="dim green")
        
def error_research(self, error_message: str):
    """Handle research error scenario."""
    
    if self.current_phase and self.current_phase in self.phases:
        self.phases[self.current_phase].error = error_message
        
    self.console.print(f"❌ Research failed: {error_message}", style="bold red")
    
def has_partial_results(self) -> bool:
    """Check if any partial results are available."""
    
    return len(self.partial_results) > 0 or any(
        p.end_time is not None for p in self.phases.values()
    )
```

This progress tracking system provides users with clear, real-time feedback about what Theodore is doing, how long operations are taking, and what to expect next, dramatically improving the user experience during long AI operations.

### Output Formatting and Multi-Format Support (12 minutes)

Let's build a comprehensive formatting system that can present Theodore's research results in multiple formats, each optimized for different use cases and audiences.

```python
# v2/src/cli/formatters/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from rich.console import Console

class BaseFormatter(ABC):
    """
    Abstract base class for all output formatters.
    
    Defines the interface that all formatters must implement
    and provides common utilities for data transformation.
    """
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        
    @abstractmethod
    def format_research_results(self, results: Dict[str, Any]) -> str:
        """Format complete research results for output."""
        pass
        
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the appropriate file extension for this format."""
        pass
        
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate that data contains required fields."""
        
        required_fields = ['company_data', 'research_status', 'timestamp']
        return all(field in data for field in required_fields)
        
    def sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or sanitize sensitive data for output."""
        
        # Create a copy to avoid modifying original data
        sanitized = data.copy()
        
        # Remove internal metadata
        sanitized.pop('_internal_metadata', None)
        sanitized.pop('_debug_info', None)
        
        # Sanitize API keys in configuration if present
        if 'configuration' in sanitized:
            config = sanitized['configuration']
            for key in config:
                if 'api_key' in key.lower() or 'secret' in key.lower():
                    config[key] = "***REDACTED***"
                    
        return sanitized

# v2/src/cli/formatters/table.py
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from typing import Dict, Any, List
import json

from .base import BaseFormatter

class RichTableFormatter(BaseFormatter):
    """
    Rich table formatter for beautiful terminal display.
    
    Creates hierarchical, color-coded tables optimized for terminal viewing
    with automatic column sizing and semantic color coding.
    """
    
    def format_research_results(self, results: Dict[str, Any]) -> str:
        """Format research results as Rich tables for terminal display."""
        
        if not self.validate_data(results):
            return self._format_error("Invalid research results data")
            
        sanitized_data = self.sanitize_data(results)
        
        # Create main layout
        layout_components = []
        
        # Company overview table
        if 'company_data' in sanitized_data:
            company_table = self._create_company_overview_table(sanitized_data['company_data'])
            layout_components.append(Panel(company_table, title="[bold cyan]Company Overview"))
            
        # Business intelligence table
        if 'business_intelligence' in sanitized_data:
            intelligence_table = self._create_intelligence_table(sanitized_data['business_intelligence'])
            layout_components.append(Panel(intelligence_table, title="[bold green]Business Intelligence"))
            
        # Similar companies table
        if 'similar_companies' in sanitized_data and sanitized_data['similar_companies']:
            similar_table = self._create_similar_companies_table(sanitized_data['similar_companies'])
            layout_components.append(Panel(similar_table, title="[bold magenta]Similar Companies"))
            
        # Research metadata
        metadata_table = self._create_metadata_table(sanitized_data)
        layout_components.append(Panel(metadata_table, title="[bold dim]Research Metadata"))
        
        # Render all components
        with self.console.capture() as capture:
            for component in layout_components:
                self.console.print(component)
                self.console.print()  # Add spacing
                
        return capture.get()
        
    def _create_company_overview_table(self, company_data: Dict[str, Any]) -> Table:
        """Create a formatted table for company overview information."""
        
        table = Table(show_header=False, show_lines=True, expand=True)
        table.add_column("Attribute", style="bold cyan", width=20)
        table.add_column("Value", style="white")
        
        # Add company information rows
        self._add_table_row(table, "Company Name", company_data.get('name', 'Unknown'))
        self._add_table_row(table, "Website", company_data.get('website', 'Not provided'))
        self._add_table_row(table, "Industry", company_data.get('industry', 'Unknown'))
        self._add_table_row(table, "Founded", company_data.get('founded_year', 'Unknown'))
        self._add_table_row(table, "Size", company_data.get('company_size', 'Unknown'))
        self._add_table_row(table, "Location", company_data.get('location', 'Unknown'))
        
        # Business model with color coding
        business_model = company_data.get('business_model', 'Unknown')
        business_model_color = self._get_business_model_color(business_model)
        table.add_row("Business Model", Text(business_model, style=business_model_color))
        
        return table
        
    def _create_intelligence_table(self, intelligence: Dict[str, Any]) -> Table:
        """Create a formatted table for business intelligence information."""
        
        table = Table(show_header=False, show_lines=True, expand=True)
        table.add_column("Category", style="bold green", width=25)
        table.add_column("Information", style="white")
        
        # Add intelligence information
        self._add_table_row(table, "Company Description", 
                          self._truncate_text(intelligence.get('description', 'Not available'), 100))
        self._add_table_row(table, "Value Proposition", 
                          self._truncate_text(intelligence.get('value_proposition', 'Not available'), 100))
        self._add_table_row(table, "Target Market", intelligence.get('target_market', 'Not available'))
        self._add_table_row(table, "Revenue Model", intelligence.get('revenue_model', 'Not available'))
        
        # Technology stack
        tech_stack = intelligence.get('technology_stack', [])
        if tech_stack:
            tech_display = ', '.join(tech_stack[:5])  # Show first 5 technologies
            if len(tech_stack) > 5:
                tech_display += f" and {len(tech_stack) - 5} more..."
            self._add_table_row(table, "Technology Stack", tech_display)
            
        return table
        
    def _create_similar_companies_table(self, similar_companies: List[Dict[str, Any]]) -> Table:
        """Create a formatted table for similar companies."""
        
        table = Table(show_header=True, expand=True)
        table.add_column("Company", style="bold")
        table.add_column("Website", style="dim")
        table.add_column("Similarity", justify="center")
        table.add_column("Industry", style="cyan")
        table.add_column("Description", style="white")
        
        for company in similar_companies[:10]:  # Show top 10 similar companies
            similarity_score = company.get('similarity_score', 0)
            similarity_display = self._format_similarity_score(similarity_score)
            
            table.add_row(
                company.get('name', 'Unknown'),
                company.get('website', 'N/A'),
                similarity_display,
                company.get('industry', 'Unknown'),
                self._truncate_text(company.get('description', ''), 50)
            )
            
        return table
        
    def _create_metadata_table(self, data: Dict[str, Any]) -> Table:
        """Create a table for research metadata and statistics."""
        
        table = Table(show_header=False, show_lines=True, expand=True)
        table.add_column("Metric", style="bold dim", width=25)
        table.add_column("Value", style="dim")
        
        # Research timing
        if 'research_duration' in data:
            self._add_table_row(table, "Research Duration", f"{data['research_duration']:.1f} seconds")
            
        # Data sources
        if 'data_sources' in data:
            sources = ', '.join(data['data_sources'])
            self._add_table_row(table, "Data Sources", sources)
            
        # AI models used
        if 'ai_models_used' in data:
            models = ', '.join(data['ai_models_used'])
            self._add_table_row(table, "AI Models", models)
            
        # Research timestamp
        if 'timestamp' in data:
            self._add_table_row(table, "Research Date", data['timestamp'])
            
        # Confidence score
        if 'confidence_score' in data:
            confidence = data['confidence_score']
            confidence_display = self._format_confidence_score(confidence)
            table.add_row("Confidence Score", confidence_display)
            
        return table
```

**JSON Formatter for API Integration:**
```python
# v2/src/cli/formatters/json_formatter.py
import json
from typing import Dict, Any
from datetime import datetime

from .base import BaseFormatter

class JSONFormatter(BaseFormatter):
    """
    JSON formatter for machine-readable output and API integration.
    
    Produces clean, well-structured JSON with proper data types
    and comprehensive metadata preservation.
    """
    
    def format_research_results(self, results: Dict[str, Any]) -> str:
        """Format research results as pretty-printed JSON."""
        
        if not self.validate_data(results):
            return json.dumps({"error": "Invalid research results data"}, indent=2)
            
        sanitized_data = self.sanitize_data(results)
        
        # Add JSON-specific metadata
        formatted_data = {
            "theodore_research": {
                "version": "2.0",
                "format": "json",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                **sanitized_data
            }
        }
        
        # Custom JSON encoder for special data types
        return json.dumps(
            formatted_data,
            indent=2,
            ensure_ascii=False,
            separators=(',', ': '),
            default=self._json_serializer
        )
        
    def _json_serializer(self, obj):
        """Custom JSON serializer for special objects."""
        
        if hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # Custom objects
            return obj.__dict__
        else:
            return str(obj)
            
    def get_file_extension(self) -> str:
        return "json"

# v2/src/cli/formatters/markdown_formatter.py
from typing import Dict, Any, List
from .base import BaseFormatter

class MarkdownFormatter(BaseFormatter):
    """
    Markdown formatter for documentation and sharing.
    
    Creates GitHub-compatible markdown with tables, sections,
    and proper formatting for documentation purposes.
    """
    
    def format_research_results(self, results: Dict[str, Any]) -> str:
        """Format research results as structured markdown."""
        
        if not self.validate_data(results):
            return "# Error\n\nInvalid research results data"
            
        sanitized_data = self.sanitize_data(results)
        
        markdown_sections = []
        
        # Title and overview
        company_name = sanitized_data.get('company_data', {}).get('name', 'Unknown Company')
        markdown_sections.append(f"# Theodore Research Report: {company_name}")
        markdown_sections.append("")
        markdown_sections.append(f"Generated on: {sanitized_data.get('timestamp', 'Unknown')}")
        markdown_sections.append("")
        
        # Company overview section
        if 'company_data' in sanitized_data:
            markdown_sections.extend(self._create_company_overview_section(sanitized_data['company_data']))
            
        # Business intelligence section
        if 'business_intelligence' in sanitized_data:
            markdown_sections.extend(self._create_intelligence_section(sanitized_data['business_intelligence']))
            
        # Similar companies section
        if 'similar_companies' in sanitized_data and sanitized_data['similar_companies']:
            markdown_sections.extend(self._create_similar_companies_section(sanitized_data['similar_companies']))
            
        # Research metadata section
        markdown_sections.extend(self._create_metadata_section(sanitized_data))
        
        return "\n".join(markdown_sections)
        
    def _create_company_overview_section(self, company_data: Dict[str, Any]) -> List[str]:
        """Create markdown section for company overview."""
        
        section = ["## Company Overview", ""]
        
        # Create overview table
        section.append("| Attribute | Value |")
        section.append("|-----------|-------|")
        
        fields = [
            ("Company Name", company_data.get('name', 'Unknown')),
            ("Website", company_data.get('website', 'Not provided')),
            ("Industry", company_data.get('industry', 'Unknown')),
            ("Founded", str(company_data.get('founded_year', 'Unknown'))),
            ("Size", company_data.get('company_size', 'Unknown')),
            ("Location", company_data.get('location', 'Unknown')),
            ("Business Model", company_data.get('business_model', 'Unknown'))
        ]
        
        for field_name, field_value in fields:
            section.append(f"| {field_name} | {self._escape_markdown(str(field_value))} |")
            
        section.append("")
        return section
        
    def _escape_markdown(self, text: str) -> str:
        """Escape special markdown characters."""
        
        escape_chars = ['|', '*', '_', '`', '[', ']', '(', ')', '#', '+', '-', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
        
    def get_file_extension(self) -> str:
        return "md"
```

**Formatter Registry and Factory:**
```python
# v2/src/cli/formatters/__init__.py
from typing import Dict, Type
from .base import BaseFormatter
from .table import RichTableFormatter
from .json_formatter import JSONFormatter
from .yaml_formatter import YAMLFormatter
from .markdown_formatter import MarkdownFormatter

class FormatterRegistry:
    """Registry for managing different output formatters."""
    
    _formatters: Dict[str, Type[BaseFormatter]] = {
        'table': RichTableFormatter,
        'json': JSONFormatter,
        'yaml': YAMLFormatter,
        'markdown': MarkdownFormatter
    }
    
    @classmethod
    def get_formatter(cls, format_name: str) -> BaseFormatter:
        """Get formatter instance for specified format."""
        
        if format_name not in cls._formatters:
            raise ValueError(f"Unknown format: {format_name}")
            
        return cls._formatters[format_name]()
        
    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Get list of all available output formats."""
        
        return list(cls._formatters.keys())
        
    @classmethod
    def register_formatter(cls, name: str, formatter_class: Type[BaseFormatter]):
        """Register a new formatter."""
        
        cls._formatters[name] = formatter_class

# Export commonly used formatters
__all__ = [
    'FormatterRegistry',
    'BaseFormatter',
    'RichTableFormatter', 
    'JSONFormatter',
    'YAMLFormatter',
    'MarkdownFormatter'
]
```

This comprehensive formatting system enables Theodore to present research results in the most appropriate format for each use case, from beautiful terminal tables for interactive use to structured JSON for programmatic processing.

### Error Handling and User Experience Excellence (8 minutes)

Let's build a comprehensive error handling system that transforms frustrating error messages into helpful guidance that gets users back on track quickly.

```python
# v2/src/cli/utils/error_handling.py
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import click
import sys
import traceback
from enum import Enum

class ErrorCategory(Enum):
    CONFIGURATION = "configuration"
    NETWORK = "network"
    API_KEY = "api_key"
    INPUT_VALIDATION = "input_validation"
    TIMEOUT = "timeout"
    PERMISSION = "permission"
    SYSTEM = "system"
    UNKNOWN = "unknown"

class CLIErrorHandler:
    """
    Comprehensive error handling for CLI operations.
    
    Provides user-friendly error messages with specific suggestions
    for resolution and recovery steps.
    """
    
    def __init__(self, console: Console, verbose: bool = False):
        self.console = console
        self.verbose = verbose
        
    async def handle_error(self, error: Exception, ctx: click.Context):
        """Handle any error with appropriate user guidance."""
        
        error_category = self._categorize_error(error)
        error_info = self._extract_error_info(error, error_category)
        
        # Display formatted error message
        self._display_error_message(error_info)
        
        # Provide specific suggestions
        self._display_suggestions(error_info)
        
        # Show debug information if verbose
        if self.verbose:
            self._display_debug_info(error, ctx)
            
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error to provide appropriate guidance."""
        
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Configuration errors
        if 'config' in error_message or 'setting' in error_message:
            return ErrorCategory.CONFIGURATION
            
        # Network connectivity errors
        if any(term in error_message for term in ['connection', 'network', 'timeout', 'dns']):
            return ErrorCategory.NETWORK
            
        # API key and authentication errors
        if any(term in error_message for term in ['api key', 'authentication', 'unauthorized', 'forbidden']):
            return ErrorCategory.API_KEY
            
        # Input validation errors
        if any(term in error_message for term in ['invalid', 'validation', 'format']):
            return ErrorCategory.INPUT_VALIDATION
            
        # Timeout errors
        if 'timeout' in error_message or error_type == 'TimeoutError':
            return ErrorCategory.TIMEOUT
            
        # Permission errors
        if any(term in error_message for term in ['permission', 'access denied', 'not allowed']):
            return ErrorCategory.PERMISSION
            
        return ErrorCategory.UNKNOWN
        
    def _extract_error_info(self, error: Exception, category: ErrorCategory) -> Dict[str, Any]:
        """Extract structured information from error."""
        
        return {
            'category': category,
            'type': type(error).__name__,
            'message': str(error),
            'suggestions': self._get_suggestions_for_category(category),
            'documentation_links': self._get_documentation_links(category),
            'recovery_steps': self._get_recovery_steps(category)
        }
        
    def _display_error_message(self, error_info: Dict[str, Any]):
        """Display formatted error message with appropriate styling."""
        
        category = error_info['category']
        
        # Category-specific styling
        category_styles = {
            ErrorCategory.CONFIGURATION: "bold red",
            ErrorCategory.NETWORK: "bold orange3",
            ErrorCategory.API_KEY: "bold yellow",
            ErrorCategory.INPUT_VALIDATION: "bold blue",
            ErrorCategory.TIMEOUT: "bold magenta",
            ErrorCategory.PERMISSION: "bold red",
            ErrorCategory.SYSTEM: "bold red",
            ErrorCategory.UNKNOWN: "bold white"
        }
        
        style = category_styles.get(category, "bold white")
        
        # Create error panel
        error_panel = Panel(
            f"[{style}]{error_info['message']}[/{style}]",
            title=f"[red]⚠️  {category.value.title()} Error",
            border_style="red",
            padding=(1, 2)
        )
        
        self.console.print(error_panel)
        
    def _display_suggestions(self, error_info: Dict[str, Any]):
        """Display specific suggestions for error resolution."""
        
        suggestions = error_info.get('suggestions', [])
        recovery_steps = error_info.get('recovery_steps', [])
        
        if not suggestions and not recovery_steps:
            return
            
        # Create suggestions table
        suggestion_table = Table(title="💡 Suggested Solutions", show_header=False, expand=True)
        suggestion_table.add_column("Step", style="bold cyan", width=4)
        suggestion_table.add_column("Action", style="white")
        
        step_number = 1
        
        # Add immediate suggestions
        for suggestion in suggestions:
            suggestion_table.add_row(f"{step_number}.", suggestion)
            step_number += 1
            
        # Add recovery steps
        for step in recovery_steps:
            suggestion_table.add_row(f"{step_number}.", step)
            step_number += 1
            
        self.console.print(suggestion_table)
        self.console.print()
        
    def _get_suggestions_for_category(self, category: ErrorCategory) -> List[str]:
        """Get specific suggestions based on error category."""
        
        suggestions = {
            ErrorCategory.CONFIGURATION: [
                "Check your configuration file: theodore config show",
                "Verify all required settings are configured",
                "Try resetting to default configuration: theodore config reset"
            ],
            ErrorCategory.NETWORK: [
                "Check your internet connection",
                "Verify proxy settings if behind a corporate firewall", 
                "Try increasing timeout with --timeout flag",
                "Check if VPN is interfering with connections"
            ],
            ErrorCategory.API_KEY: [
                "Verify your API keys are correctly set in environment variables",
                "Check API key permissions and quotas",
                "Try regenerating API keys if they're expired",
                "Run: theodore config validate to check API connectivity"
            ],
            ErrorCategory.INPUT_VALIDATION: [
                "Double-check the company name spelling and format",
                "Ensure website URL includes http:// or https://",
                "Try using quotes around company names with special characters"
            ],
            ErrorCategory.TIMEOUT: [
                "Increase timeout with --timeout <seconds> flag",
                "Try using --no-domain-discovery for faster research",
                "Check network connectivity for slow responses",
                "Break research into smaller batches if processing multiple companies"
            ],
            ErrorCategory.PERMISSION: [
                "Check file system permissions for save location",
                "Ensure Theodore has access to required directories",
                "Try running with appropriate permissions or different save location"
            ]
        }
        
        return suggestions.get(category, [
            "Try the operation again",
            "Check the documentation for this feature",
            "Report the issue if it persists"
        ])
        
    def _get_recovery_steps(self, category: ErrorCategory) -> List[str]:
        """Get specific recovery steps for each error category."""
        
        recovery_steps = {
            ErrorCategory.CONFIGURATION: [
                "Run 'theodore config init' to recreate configuration",
                "Check environment variables: env | grep THEODORE"
            ],
            ErrorCategory.NETWORK: [
                "Test basic connectivity: ping google.com",
                "Check firewall and proxy settings"
            ],
            ErrorCategory.API_KEY: [
                "Verify API key format and permissions",
                "Check API service status pages"
            ]
        }
        
        return recovery_steps.get(category, [])
        
    def _display_debug_info(self, error: Exception, ctx: click.Context):
        """Display detailed debug information when verbose mode is enabled."""
        
        debug_table = Table(title="🔍 Debug Information", show_header=False)
        debug_table.add_column("Property", style="bold dim", width=15)
        debug_table.add_column("Value", style="dim")
        
        # Add debug information
        debug_table.add_row("Error Type", type(error).__name__)
        debug_table.add_row("Python Version", sys.version.split()[0])
        debug_table.add_row("Command", ctx.command.name if ctx.command else "Unknown")
        debug_table.add_row("Parameters", str(ctx.params) if ctx.params else "None")
        
        self.console.print(debug_table)
        
        # Show full traceback in verbose mode
        if self.verbose:
            self.console.print("\n[bold dim]Full Traceback:[/bold dim]")
            self.console.print(traceback.format_exc(), style="dim")
            
    def suggest_company_name_format(self, company_name: str):
        """Provide specific suggestions for company name formatting."""
        
        suggestions = []
        
        if len(company_name) < 2:
            suggestions.append(f"Company name too short: '{company_name}'. Try the full company name.")
            
        if company_name.isdigit():
            suggestions.append("Company name appears to be only numbers. Include company name text.")
            
        if not any(c.isalpha() for c in company_name):
            suggestions.append("Company name should contain letters. Check spelling.")
            
        # Suggest common corrections
        if company_name.lower() in ['apple', 'google', 'microsoft', 'amazon']:
            suggestions.append(f"Did you mean '{company_name.title()} Inc'?")
            
        if suggestions:
            for suggestion in suggestions:
                self.console.print(f"💡 {suggestion}", style="yellow")
                
    def suggest_website_correction(self, website: str, corrected_url: str):
        """Suggest website URL corrections."""
        
        self.console.print(f"❌ Invalid URL: {website}", style="red")
        self.console.print(f"💡 Suggested correction: {corrected_url}", style="green")
        self.console.print("💡 URLs should include http:// or https://", style="dim")
```

**Input Validation with Helpful Suggestions:**
```python
# v2/src/cli/utils/validation.py
import re
from typing import Optional
from urllib.parse import urlparse

class InputValidator:
    """Comprehensive input validation with helpful error suggestions."""
    
    def validate_company_name(self, company_name: str) -> bool:
        """Validate company name format and content."""
        
        if not company_name or len(company_name.strip()) < 2:
            return False
            
        # Must contain at least one letter
        if not any(c.isalpha() for c in company_name):
            return False
            
        # Reasonable length limits
        if len(company_name) > 100:
            return False
            
        return True
        
    def validate_website_url(self, url: str) -> bool:
        """Validate website URL format."""
        
        if not url:
            return False
            
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and bool(parsed.scheme)
        except Exception:
            return False
            
    def suggest_url_correction(self, url: str) -> str:
        """Suggest corrections for malformed URLs."""
        
        url = url.strip()
        
        # Add https:// if missing scheme
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
            
        # Remove common typos
        url = url.replace('www.www.', 'www.')
        url = url.replace('http://https://', 'https://')
        
        return url
```

This error handling system transforms potentially frustrating experiences into guided problem-solving sessions, helping users quickly resolve issues and continue being productive with Theodore.

### File Operations and Result Persistence (6 minutes)

Let's implement comprehensive file operations that allow users to save research results in multiple formats with proper error handling and user feedback.

```python
# v2/src/cli/utils/file_operations.py
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import asyncio
import aiofiles

class FileOperationManager:
    """
    Comprehensive file operations for saving and loading research results.
    
    Handles multiple formats, directory creation, backup management,
    and provides user feedback during operations.
    """
    
    def __init__(self, console: Console):
        self.console = console
        
    async def save_results(
        self,
        results: Dict[str, Any],
        file_path: str,
        format_name: str,
        formatter_instance: Any,
        create_backup: bool = True
    ) -> bool:
        """Save research results to file with comprehensive error handling."""
        
        try:
            # Resolve and validate file path
            resolved_path = Path(file_path).resolve()
            
            # Create directory if it doesn't exist
            await self._ensure_directory_exists(resolved_path.parent)
            
            # Create backup if file exists and backup is requested
            if create_backup and resolved_path.exists():
                await self._create_backup_file(resolved_path)
                
            # Format the data
            with self.console.status(f"[bold blue]Formatting data as {format_name}..."):
                formatted_content = formatter_instance.format_research_results(results)
                
            # Write file with progress indication
            await self._write_file_with_progress(resolved_path, formatted_content)
            
            # Verify file was written correctly
            if await self._verify_file_written(resolved_path, len(formatted_content)):
                self.console.print(f"✅ Results saved to: [bold green]{resolved_path}[/bold green]")
                self._display_file_info(resolved_path)
                return True
            else:
                self.console.print(f"❌ Failed to verify saved file: {resolved_path}", style="bold red")
                return False
                
        except PermissionError:
            self.console.print(f"❌ Permission denied: Cannot write to {file_path}", style="bold red")
            self.console.print("💡 Try a different location or check file permissions", style="yellow")
            return False
            
        except OSError as e:
            self.console.print(f"❌ File system error: {e}", style="bold red")
            self.console.print("💡 Check disk space and file path validity", style="yellow")
            return False
            
        except Exception as e:
            self.console.print(f"❌ Unexpected error saving file: {e}", style="bold red")
            return False
            
    async def _ensure_directory_exists(self, directory_path: Path):
        """Create directory and any necessary parent directories."""
        
        if not directory_path.exists():
            self.console.print(f"📁 Creating directory: {directory_path}", style="dim")
            directory_path.mkdir(parents=True, exist_ok=True)
            
    async def _create_backup_file(self, file_path: Path):
        """Create a backup of existing file before overwriting."""
        
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        counter = 1
        
        # Find unique backup filename
        while backup_path.exists():
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup.{counter}")
            counter += 1
            
        # Copy existing file to backup
        backup_path.write_bytes(file_path.read_bytes())
        self.console.print(f"💾 Created backup: [dim]{backup_path}[/dim]")
        
    async def _write_file_with_progress(self, file_path: Path, content: str):
        """Write file content with progress indication for large files."""
        
        content_bytes = content.encode('utf-8')
        
        # Show progress for larger files
        if len(content_bytes) > 100_000:  # 100KB
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Writing file..."),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("Writing", total=None)
                
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    # Write in chunks for very large files
                    chunk_size = 8192
                    for i in range(0, len(content), chunk_size):
                        chunk = content[i:i + chunk_size]
                        await f.write(chunk)
                        progress.advance(task)
                        
                        # Allow other coroutines to run
                        if i % (chunk_size * 10) == 0:
                            await asyncio.sleep(0.001)
        else:
            # Direct write for smaller files
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
                
    async def _verify_file_written(self, file_path: Path, expected_size: int) -> bool:
        """Verify that file was written correctly."""
        
        if not file_path.exists():
            return False
            
        # Check file size is reasonable
        actual_size = file_path.stat().st_size
        
        # Allow for some variation due to encoding differences
        size_tolerance = max(100, expected_size * 0.05)  # 5% tolerance or 100 bytes
        
        return abs(actual_size - expected_size) <= size_tolerance
        
    def _display_file_info(self, file_path: Path):
        """Display helpful information about the saved file."""
        
        stat = file_path.stat()
        file_size = stat.st_size
        
        # Format file size nicely
        if file_size < 1024:
            size_display = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_display = f"{file_size / 1024:.1f} KB"
        else:
            size_display = f"{file_size / (1024 * 1024):.1f} MB"
            
        self.console.print(f"📊 File size: {size_display}", style="dim")
        
        # Suggest next steps based on file type
        extension = file_path.suffix.lower()
        if extension == '.json':
            self.console.print("💡 Use with: cat, jq, or import into other tools", style="dim")
        elif extension == '.md':
            self.console.print("💡 View with: cat, or open in any markdown viewer", style="dim")
        elif extension == '.yaml' or extension == '.yml':
            self.console.print("💡 Use with: cat, or import as configuration", style="dim")

    def generate_suggested_filename(
        self,
        company_name: str,
        format_name: str,
        include_timestamp: bool = True
    ) -> str:
        """Generate a suggested filename based on company name and format."""
        
        # Clean company name for filename
        clean_name = re.sub(r'[^\w\-_\. ]', '', company_name)
        clean_name = re.sub(r'\s+', '_', clean_name.strip())
        clean_name = clean_name.lower()
        
        # Add timestamp if requested
        timestamp_suffix = ""
        if include_timestamp:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamp_suffix = f"_{timestamp}"
            
        # Get appropriate extension
        extensions = {
            'json': 'json',
            'yaml': 'yaml', 
            'markdown': 'md',
            'table': 'txt'
        }
        
        extension = extensions.get(format_name, 'txt')
        
        return f"theodore_research_{clean_name}{timestamp_suffix}.{extension}"
        
    async def load_previous_results(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load previously saved research results for comparison or continuation."""
        
        try:
            resolved_path = Path(file_path).resolve()
            
            if not resolved_path.exists():
                self.console.print(f"📁 File not found: {file_path}", style="yellow")
                return None
                
            # Determine format from extension
            extension = resolved_path.suffix.lower()
            
            async with aiofiles.open(resolved_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                
            if extension == '.json':
                return json.loads(content)
            elif extension in ['.yaml', '.yml']:
                import yaml
                return yaml.safe_load(content)
            else:
                self.console.print(f"⚠️  Cannot load {extension} files as structured data", style="yellow")
                return None
                
        except json.JSONDecodeError:
            self.console.print(f"❌ Invalid JSON format in {file_path}", style="red")
            return None
        except Exception as e:
            self.console.print(f"❌ Error loading file: {e}", style="red")
            return None
```

**Integration with Main Research Command:**
```python
async def _format_and_display_results(
    results: Dict[str, Any],
    output_format: str,
    save_path: Optional[str],
    progress_tracker: ResearchProgressTracker
):
    """Format results and optionally save to file."""
    
    # Get appropriate formatter
    formatter = FormatterRegistry.get_formatter(output_format)
    
    # Format results for display
    formatted_output = formatter.format_research_results(results)
    
    # Display results
    if output_format == 'table':
        # For table format, formatter handles console output
        pass  # Output already displayed by Rich formatter
    else:
        # For other formats, display content
        console.print(formatted_output)
        
    # Save to file if requested
    if save_path:
        file_manager = FileOperationManager(console)
        
        # Generate suggested filename if user just provided directory
        if Path(save_path).is_dir():
            company_name = results.get('company_data', {}).get('name', 'unknown')
            suggested_name = file_manager.generate_suggested_filename(company_name, output_format)
            save_path = str(Path(save_path) / suggested_name)
            console.print(f"📝 Using filename: [dim]{suggested_name}[/dim]")
            
        success = await file_manager.save_results(
            results, save_path, output_format, formatter
        )
        
        if not success:
            console.print("💡 Try using --save with a different file path", style="yellow")
```

This file operations system provides users with reliable, user-friendly file saving capabilities with helpful feedback and error recovery options.

### Conclusion and Integration Testing (5 minutes)

Let's wrap up our CLI research command implementation by creating comprehensive integration tests and reviewing the complete system we've built.

```python
# v2/tests/e2e/test_research_cli.py
import pytest
import tempfile
import json
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import AsyncMock, patch

from src.cli.commands.research import research
from src.infrastructure.container import ContainerFactory

class TestResearchCLIIntegration:
    """
    End-to-end tests for the research CLI command.
    
    Tests the complete command execution pipeline including
    container integration, progress tracking, and output formatting.
    """
    
    @pytest.fixture
    def cli_runner(self):
        return CliRunner()
        
    @pytest.fixture
    def temp_output_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
            
    @pytest.fixture
    def mock_research_results(self):
        return {
            "company_data": {
                "name": "Test Company Inc",
                "website": "https://test-company.com",
                "industry": "Technology",
                "founded_year": 2020,
                "business_model": "B2B SaaS"
            },
            "business_intelligence": {
                "description": "A test company for demonstration purposes",
                "value_proposition": "Provides testing services",
                "target_market": "Software developers"
            },
            "similar_companies": [
                {
                    "name": "Similar Corp",
                    "website": "https://similar.com",
                    "similarity_score": 0.85,
                    "industry": "Technology"
                }
            ],
            "research_status": "completed",
            "timestamp": "2024-01-01T12:00:00Z",
            "research_duration": 45.2
        }
        
    @pytest.mark.asyncio
    async def test_basic_research_command(self, cli_runner, mock_research_results):
        """Test basic research command execution."""
        
        with patch('src.cli.commands.research._initialize_container') as mock_container:
            with patch('src.cli.commands.research._execute_research_with_progress') as mock_research:
                # Setup mocks
                mock_research.return_value = mock_research_results
                
                # Execute command
                result = cli_runner.invoke(research, ['Test Company Inc', 'test-company.com'])
                
                # Verify success
                assert result.exit_code == 0
                assert "Research completed successfully" in result.output
                assert "Test Company Inc" in result.output
                
    @pytest.mark.asyncio 
    async def test_json_output_format(self, cli_runner, mock_research_results, temp_output_dir):
        """Test JSON output format and file saving."""
        
        output_file = temp_output_dir / "test_output.json"
        
        with patch('src.cli.commands.research._initialize_container'):
            with patch('src.cli.commands.research._execute_research_with_progress') as mock_research:
                mock_research.return_value = mock_research_results
                
                # Execute command with JSON output
                result = cli_runner.invoke(research, [
                    'Test Company Inc',
                    '--output', 'json',
                    '--save', str(output_file)
                ])
                
                # Verify command success
                assert result.exit_code == 0
                
                # Verify file was created and contains valid JSON
                assert output_file.exists()
                
                with open(output_file, 'r') as f:
                    saved_data = json.load(f)
                    
                assert 'theodore_research' in saved_data
                assert saved_data['theodore_research']['company_data']['name'] == 'Test Company Inc'
                
    @pytest.mark.asyncio
    async def test_error_handling_invalid_company(self, cli_runner):
        """Test error handling for invalid company names."""
        
        # Test with invalid company name
        result = cli_runner.invoke(research, [''])
        
        assert result.exit_code != 0
        assert "Invalid company name" in result.output or "Error" in result.output
        
    @pytest.mark.asyncio
    async def test_timeout_handling(self, cli_runner):
        """Test timeout handling and graceful shutdown."""
        
        with patch('src.cli.commands.research._execute_research_with_progress') as mock_research:
            # Mock timeout error
            mock_research.side_effect = asyncio.TimeoutError()
            
            result = cli_runner.invoke(research, [
                'Test Company',
                '--timeout', '1'  # Very short timeout
            ])
            
            assert "timed out" in result.output.lower()
            assert "increase timeout" in result.output.lower()
            
    @pytest.mark.asyncio
    async def test_verbose_mode(self, cli_runner, mock_research_results):
        """Test verbose mode provides additional information."""
        
        with patch('src.cli.commands.research._initialize_container'):
            with patch('src.cli.commands.research._execute_research_with_progress') as mock_research:
                mock_research.return_value = mock_research_results
                
                # Execute with verbose flag
                result = cli_runner.invoke(research, [
                    'Test Company',
                    '--verbose'
                ])
                
                assert result.exit_code == 0
                # Verbose mode should provide additional details
                assert len(result.output) > 100  # More detailed output
                
    @pytest.mark.asyncio
    async def test_config_override(self, cli_runner, mock_research_results):
        """Test configuration override functionality."""
        
        with patch('src.cli.commands.research._initialize_container') as mock_container:
            with patch('src.cli.commands.research._execute_research_with_progress') as mock_research:
                mock_research.return_value = mock_research_results
                
                # Execute with config override
                result = cli_runner.invoke(research, [
                    'Test Company',
                    '--config-override', 'timeout=120',
                    '--config-override', 'ai_provider=bedrock'
                ])
                
                assert result.exit_code == 0
                # Verify config overrides were passed to container
                mock_container.assert_called_once()
                
    def test_help_documentation(self, cli_runner):
        """Test that help documentation is comprehensive and helpful."""
        
        result = cli_runner.invoke(research, ['--help'])
        
        assert result.exit_code == 0
        assert "Research a company" in result.output
        assert "Examples:" in result.output
        assert "--output" in result.output
        assert "--verbose" in result.output
        assert "--timeout" in result.output
        
    @pytest.mark.asyncio
    async def test_progress_display_integration(self, cli_runner, mock_research_results):
        """Test that progress display integrates correctly with command execution."""
        
        progress_updates = []
        
        def mock_progress_callback(phase, progress, message):
            progress_updates.append((phase, progress, message))
            
        with patch('src.cli.commands.research._initialize_container'):
            with patch('src.cli.commands.research._execute_research_with_progress') as mock_research:
                # Mock research execution with progress callbacks
                async def mock_execute(*args, **kwargs):
                    # Simulate progress updates
                    callback = kwargs.get('progress_callback') 
                    if callback:
                        callback('initialization', 0.1, 'Starting research')
                        callback('ai_research', 0.5, 'Gathering intelligence')
                        callback('completed', 1.0, 'Research complete')
                    return mock_research_results
                    
                mock_research.side_effect = mock_execute
                
                result = cli_runner.invoke(research, ['Test Company'])
                
                assert result.exit_code == 0
                # Verify progress updates were captured
                assert len(progress_updates) >= 3
```

**Performance and Load Testing:**
```python
@pytest.mark.performance
class TestResearchCLIPerformance:
    """Performance tests for CLI research command."""
    
    @pytest.mark.asyncio
    async def test_command_startup_time(self, cli_runner):
        """Test that command starts up quickly."""
        
        import time
        
        start_time = time.time()
        
        # Test help command (minimal initialization)
        result = cli_runner.invoke(research, ['--help'])
        
        startup_time = time.time() - start_time
        
        assert result.exit_code == 0
        assert startup_time < 2.0  # Should start within 2 seconds
        
    @pytest.mark.asyncio
    async def test_large_result_formatting(self, cli_runner, temp_output_dir):
        """Test performance with large result datasets."""
        
        # Create large mock dataset
        large_results = {
            "company_data": {"name": "Large Corp"},
            "similar_companies": [
                {
                    "name": f"Company {i}",
                    "similarity_score": 0.8,
                    "description": "A" * 500  # Large description
                }
                for i in range(100)  # 100 similar companies
            ],
            "research_status": "completed",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        with patch('src.cli.commands.research._initialize_container'):
            with patch('src.cli.commands.research._execute_research_with_progress') as mock_research:
                mock_research.return_value = large_results
                
                start_time = time.time()
                
                result = cli_runner.invoke(research, [
                    'Large Corp',
                    '--output', 'json'
                ])
                
                processing_time = time.time() - start_time
                
                assert result.exit_code == 0
                assert processing_time < 10.0  # Should process within 10 seconds
```

**Summary of the Complete CLI Research Command:**

In this comprehensive tutorial, we've built a production-grade CLI research command that:

1. **Seamless Container Integration**: Properly wires with Theodore's dependency injection system for clean, testable code

2. **Real-Time Progress Tracking**: Rich progress bars with phase-specific updates that keep users informed during long AI operations

3. **Multiple Output Formats**: Table, JSON, YAML, and Markdown formats optimized for different use cases

4. **Comprehensive Error Handling**: User-friendly error messages with specific suggestions for resolution

5. **File Operations**: Robust saving capabilities with backup management and verification

6. **Professional UX**: Graceful shutdown, input validation, configuration overrides, and helpful documentation

7. **Extensive Testing**: Unit tests, integration tests, and performance validation

The command provides a beautiful, reliable interface to Theodore's AI capabilities while maintaining the high standards users expect from professional developer tools. The modular design ensures each component can be tested independently while the integration tests validate the complete user experience.

This implementation demonstrates how thoughtful UX design, comprehensive error handling, and robust engineering combine to create CLI tools that users genuinely enjoy using.

## Estimated Time: 5-6 hours