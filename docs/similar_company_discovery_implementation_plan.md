# Similar Company Discovery - Implementation Plan

## Overview
Build a feature that discovers, validates, and stores similar companies for any given company in Theodore's database.

## Feature Flow
```
Input: Company → LLM Discovery → Crawl Candidates → Similarity Validation → Store Results
```

## Phase 1: Core Discovery Engine (Week 1)

### 1.1 LLM Company Discovery Service
**File**: `src/company_discovery.py`

```python
class CompanyDiscoveryService:
    def discover_similar_companies(self, target_company: CompanyData) -> List[CompanySuggestion]
    def _create_discovery_prompt(self, company: CompanyData) -> str
    def _parse_llm_suggestions(self, llm_response: str) -> List[CompanySuggestion]
```

**Tasks**:
- [ ] Create discovery prompt template with company context
- [ ] Integrate with existing Bedrock client for LLM calls
- [ ] Parse LLM response to extract company names and URLs
- [ ] Handle LLM hallucinations and invalid responses

### 1.2 Similarity Validation Engine  
**File**: `src/similarity_validator.py`

```python
class SimilarityValidator:
    def validate_similarity(self, original: CompanyData, candidate: CompanyData) -> SimilarityResult
    def _structured_comparison(self, comp_a: CompanyData, comp_b: CompanyData) -> float
    def _embedding_similarity(self, comp_a: CompanyData, comp_b: CompanyData) -> float
    def _llm_judge_similarity(self, comp_a: CompanyData, comp_b: CompanyData) -> dict
```

**Tasks**:
- [ ] Implement structured field comparison logic
- [ ] Add embedding-based similarity using existing embeddings
- [ ] Create LLM judge with structured prompt
- [ ] Build voting system (2/3 methods must agree)

### 1.3 Data Models
**File**: `src/models.py` (extend existing)

```python
class CompanySuggestion(BaseModel):
    company_name: str
    website_url: str
    suggested_reason: str
    confidence_score: float

class SimilarityResult(BaseModel):
    is_similar: bool
    confidence: float
    methods_used: List[str]
    scores: Dict[str, float]
    reasoning: List[str]

class CompanySimilarity(BaseModel):
    original_company_id: str
    similar_company_id: str
    similarity_score: float
    discovery_method: str
    validated_at: datetime
```

**Tasks**:
- [ ] Define data models for discovery workflow
- [ ] Add similarity relationship tracking
- [ ] Extend existing CompanyData model if needed

## Phase 2: Integration & Pipeline (Week 2)

### 2.1 Discovery Pipeline Integration
**File**: `src/similarity_pipeline.py`

```python
class SimilarityDiscoveryPipeline:
    def discover_and_validate_similar_companies(self, company_id: str) -> List[CompanyData]
    def _crawl_candidate_companies(self, suggestions: List[CompanySuggestion]) -> List[CompanyData] 
    def _store_similarity_relationships(self, results: List[SimilarityResult])
```

**Tasks**:
- [ ] Integrate with existing crawl4ai_scraper for candidate crawling
- [ ] Add rate limiting and error handling for bulk discovery
- [ ] Create batch processing for multiple companies
- [ ] Add progress tracking and logging

### 2.2 Vector Storage Updates
**File**: `src/pinecone_client.py` (extend existing)

```python
class PineconeClient:
    def store_similarity_relationships(self, relationships: List[CompanySimilarity])
    def find_similar_companies(self, company_id: str, limit: int = 10) -> List[CompanyData]
    def get_similarity_score(self, company_a_id: str, company_b_id: str) -> float
```

**Tasks**:
- [ ] Extend Pinecone metadata to include similarity relationships
- [ ] Add similarity search methods
- [ ] Implement similarity relationship storage
- [ ] Add bulk similarity queries

## Phase 3: API & User Interface (Week 3)

### 3.1 CLI Commands
**File**: `src/main_pipeline.py` (extend existing)

```python
# New CLI commands
def discover_similar_companies_cli(company_name: str, limit: int = 10)
def batch_discover_similarities_cli(csv_file: str)
def query_similar_companies_cli(company_name: str)
```

**Tasks**:
- [ ] Add CLI command for single company discovery
- [ ] Add CLI command for batch similarity discovery
- [ ] Add CLI command for querying existing similarities
- [ ] Integrate with existing pipeline architecture

### 3.2 API Endpoints (Future)
**File**: `src/api.py` (new file)

```python
@app.post("/discover-similar")
def discover_similar_companies(company_id: str)

@app.get("/similar-companies/{company_id}")  
def get_similar_companies(company_id: str)
```

**Tasks**:
- [ ] Create FastAPI endpoints for discovery
- [ ] Add similarity search endpoints
- [ ] Implement rate limiting and authentication
- [ ] Add API documentation

## Phase 4: Quality & Performance (Week 4)

### 4.1 Quality Assurance
**File**: `tests/test_similarity_discovery.py`

**Tasks**:
- [ ] Unit tests for similarity validation methods
- [ ] Integration tests for discovery pipeline  
- [ ] Test cases for edge cases (no similarities found, API failures)
- [ ] Performance tests for bulk discovery

### 4.2 Configuration & Monitoring
**File**: `config/settings.py` (extend existing)

**Tasks**:
- [ ] Add similarity threshold configurations
- [ ] Add discovery rate limiting settings
- [ ] Add monitoring and logging configurations
- [ ] Create similarity quality metrics

## Implementation Priority

### Week 1 - MVP Core
1. **LLM Discovery Service** - Basic similar company suggestions
2. **Similarity Validator** - Multi-method validation system
3. **Data Models** - Support new similarity data structures

### Week 2 - Integration  
1. **Discovery Pipeline** - End-to-end workflow
2. **Crawling Integration** - Reuse existing scraper
3. **Storage Integration** - Extend Pinecone functionality

### Week 3 - User Interface
1. **CLI Commands** - User-facing discovery tools
2. **Query Interface** - Search and retrieve similarities
3. **Batch Processing** - Handle multiple companies

### Week 4 - Production Ready
1. **Quality Assurance** - Testing and validation
2. **Performance Optimization** - Speed and cost efficiency
3. **Monitoring** - Track usage and quality metrics

## Success Metrics
- **Discovery Rate**: % of companies that find at least 3 valid similar companies
- **Validation Accuracy**: % of LLM suggestions that pass similarity validation
- **Processing Speed**: Companies processed per hour
- **User Satisfaction**: Quality of discovered similarities (manual review)

## Risk Mitigation
- **LLM Hallucinations**: Validate all suggestions with web crawling
- **Rate Limits**: Implement exponential backoff and batching
- **Cost Control**: Set daily limits on LLM calls and crawling
- **Quality Control**: Manual spot-checking of similarity results

## Next Steps
Ready to start implementation? Recommended starting point: Phase 1.1 - LLM Company Discovery Service