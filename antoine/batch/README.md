# Antoine Batch Processing System

## Overview
The antoine batch processing system enables parallel processing of multiple companies using the reliable 4-phase pipeline (discovery → selection → crawling → extraction) with resource pooling and intelligent concurrency control.

## Architecture

### Core Components

1. **AntoineBatchProcessor** (`batch_processor.py`)
   - Thread-based parallel execution with semaphore control
   - Resource pooling for scraper instances
   - Progress tracking and error isolation
   - Configurable concurrency levels

2. **Integration with Main Pipeline**
   - `AntoineScraperAdapter.batch_scrape_companies()` method
   - Drop-in compatibility with existing pipeline
   - Maintains same CompanyData output format

### Key Features

- **Parallel Company Processing**: Process multiple companies concurrently
- **Resource Pooling**: Reuse scraper instances for efficiency
- **Error Isolation**: Failures don't affect other companies in batch
- **Progress Tracking**: Real-time progress per company
- **Adaptive Timeouts**: Configurable timeout management
- **Thread Safety**: Proper synchronization for shared resources

## Usage

### Basic Usage
```python
from antoine.batch.batch_processor import AntoineBatchProcessor
from src.models import CompanyIntelligenceConfig

# Create batch processor
batch_processor = AntoineBatchProcessor(
    config=CompanyIntelligenceConfig(),
    max_concurrent_companies=3,
    enable_resource_pooling=True
)

# Process companies
companies = [
    {"name": "Stripe", "website": "https://stripe.com"},
    {"name": "Shopify", "website": "https://shopify.com"}
]

result = batch_processor.process_batch(companies)
print(f"Processed {result.successful}/{result.total_companies} successfully")
```

### Integration with Main Pipeline
```python
from src.main_pipeline import TheodoreIntelligencePipeline

pipeline = TheodoreIntelligencePipeline(config)

# The pipeline now automatically uses antoine batch processing
companies = [CompanyData(name="Example", website="https://example.com")]
results = pipeline.batch_process_companies(companies)
```

## Performance Results

### Simple Test (5 Companies)
- **Success Rate**: 100% (5/5)
- **Total Time**: 104 seconds
- **Throughput**: 2.9 companies/minute
- **Speed Improvement**: 2.3x over sequential
- **Parallel Efficiency**: 233%

### Resource Usage
- **Average Pages per Company**: 16.6
- **Average Time per Company**: 48.45 seconds
- **Total Pages Crawled**: 83

## Configuration Options

### Concurrency Control
- `max_concurrent_companies`: Number of companies to process in parallel (default: 3)
- Recommended: 3-5 for optimal balance of speed and resource usage

### Resource Pooling
- `enable_resource_pooling`: Reuse scraper instances (default: True)
- Reduces initialization overhead for large batches

## Testing

### Available Tests
1. **Simple Test** (`test_batch_simple.py`)
   - Basic 5-company test
   - Validates core functionality

2. **Parallel Test** (`test_batch_parallel.py`)
   - Visualizes parallel execution
   - Shows concurrency behavior

3. **Stress Test** (`test_batch_stress.py`)
   - Tests with 10-20+ companies
   - Memory and performance analysis

### Running Tests
```bash
# Simple test
python3 antoine/test/test_batch_simple.py

# Parallel visualization
python3 antoine/test/test_batch_parallel.py

# Stress test with custom parameters
python3 antoine/test/test_batch_stress.py 20 5  # 20 companies, 5 concurrent
```

## Bottlenecks and Optimization

### Current Bottlenecks
1. **LLM API Calls**: Nova Pro extraction ~10-15s per company
2. **Large Websites**: Complex sites with many pages take longer
3. **Network I/O**: Page crawling is inherently I/O bound

### Future Optimizations
1. **LLM Request Batching**: Combine multiple extraction requests
2. **Adaptive Concurrency**: Adjust based on site complexity
3. **Connection Pooling**: Share HTTP sessions across scrapers
4. **Caching Layer**: Cache discovery results for repeat processing

## Error Handling

The batch processor implements robust error handling:
- Individual company failures don't stop the batch
- Errors are collected and reported per company
- Progress tracking continues despite failures
- Resource cleanup guaranteed via context managers

## Comparison to Previous Batch Processors

| Feature | Antoine Batch | Previous Batch |
|---------|--------------|----------------|
| Success Rate | 100% | ~70-80% |
| Speed Improvement | 2.3x | 1.5x |
| Error Isolation | ✅ Yes | ❌ No |
| Progress Tracking | ✅ Per-phase | ⚠️ Limited |
| Resource Pooling | ✅ Yes | ❌ No |
| Architecture | Clean 4-phase | Complex |

## Best Practices

1. **Concurrency Setting**: Start with 3, increase gradually based on resources
2. **Batch Size**: 20-50 companies per batch for optimal throughput
3. **Error Monitoring**: Check `result.errors` for failed companies
4. **Resource Cleanup**: Always call `shutdown()` when done

## Integration with Google Sheets

The batch processor can be integrated with Google Sheets for input/output:
```python
# Read companies from sheet
sheets_client = GoogleSheetsServiceClient()
companies = sheets_client.read_companies(spreadsheet_id)

# Process batch
result = batch_processor.process_batch(companies)

# Write results back
sheets_client.update_batch_results(spreadsheet_id, result)
```

## Production Considerations

1. **Rate Limiting**: Implement delays between batches for API limits
2. **Monitoring**: Add logging and metrics collection
3. **Persistence**: Save progress for resume capability
4. **Scaling**: Consider distributed processing for 100+ companies