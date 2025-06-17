# SaaS Business Model Classification - Implementation Plan

## Overview
Mandatory SaaS classification feature that analyzes and categorizes companies using a 59-category taxonomy from existing Theodore data. Classification becomes Phase 5 of the intelligent scraping pipeline and is applied to all operations.

## Phase 1: Foundation & Data Model (Week 1-2)

### 1.1 Data Model Updates
**File: `src/models.py`**

```python
# Add to CompanyData class
class CompanyData(BaseModel):
    # ... existing fields ...
    
    # Classification fields
    saas_classification: Optional[str] = None
    classification_confidence: Optional[float] = None
    classification_justification: Optional[str] = None
    classification_timestamp: Optional[datetime] = None
    classification_model_version: Optional[str] = "v1.0"
    is_saas: Optional[bool] = None  # Quick boolean for filtering
```

**File: `src/models.py` - New Classification Models**

```python
class SaaSCategory(str, Enum):
    # SaaS Verticals
    ADTECH = "AdTech"
    ASSET_MANAGEMENT = "AssetManagement"
    BILLING = "Billing"
    BIO_LS = "Bio/LS"
    # ... all 33 SaaS categories
    
    # Non-SaaS Categories  
    ADVERTISING_MEDIA = "Advertising & Media Services"
    BIOPHARMA_RD = "Biopharma R&D"
    # ... all 25 Non-SaaS categories
    
    UNCLASSIFIED = "Unclassified"

class ClassificationResult(BaseModel):
    category: SaaSCategory
    confidence: float
    justification: str
    model_version: str
    timestamp: datetime
    is_saas: bool
```

### 1.2 Database Schema Migration
**File: `scripts/database/migrate_classification_fields.py`**

```python
def migrate_pinecone_schema():
    """Add classification fields to existing Pinecone vectors"""
    # Update metadata schema
    # Batch update existing records with null classification
    # Verify migration success
```

### 1.3 Classification Service Core
**File: `src/classification/saas_classifier.py`**

```python
class SaaSBusinessModelClassifier:
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.taxonomy = self._load_classification_taxonomy()
        self.prompt_template = self._load_classification_prompt()
    
    def classify_company(self, company_data: CompanyData) -> ClassificationResult:
        """Main classification method"""
        
    def _prepare_classification_input(self, company_data) -> str:
        """Extract relevant content for classification"""
        
    def _parse_classification_response(self, response) -> ClassificationResult:
        """Parse LLM response into structured result"""
        
    def _validate_classification(self, result) -> bool:
        """Validate classification result quality"""
```

**File: `src/classification/classification_prompts.py`**

```python
SAAS_CLASSIFICATION_PROMPT = """
You are an expert business model analyst. Your primary function is to accurately 
analyze and classify companies based on their publicly stated business model.

COMPANY DATA TO ANALYZE:
Company Name: {company_name}
Website: {website}
Business Intelligence: {business_intelligence}
Products/Services: {products_services}
Value Proposition: {value_proposition}

CLASSIFICATION TAXONOMY:
{taxonomy}

INSTRUCTIONS:
1. Analyze the provided company data
2. Choose the single best-fit classification
3. Provide confidence score (0.0-1.0)
4. Provide one-sentence justification

OUTPUT FORMAT:
Classification: [category]
Confidence: [0.0-1.0]
Justification: [one sentence based on evidence]
Is_SaaS: [true/false]
"""
```

### 1.4 Pipeline Integration
**File: `src/main_pipeline.py`**

```python
class TheodoreIntelligencePipeline:
    def __init__(self, ...):
        # ... existing initialization ...
        self.classifier = SaaSBusinessModelClassifier(self.bedrock_client)
    
    def process_single_company(self, name: str, website: str) -> CompanyData:
        # Existing phases 1-4
        company_data = self._run_four_phase_pipeline(name, website)
        
        # Phase 5: Mandatory Classification
        try:
            classification = self.classifier.classify_company(company_data)
            company_data.saas_classification = classification.category.value
            company_data.classification_confidence = classification.confidence
            company_data.classification_justification = classification.justification
            company_data.classification_timestamp = classification.timestamp
            company_data.is_saas = classification.is_saas
            
            progress_logger.log_progress(job_id, "classification_complete", {
                "category": classification.category.value,
                "confidence": classification.confidence
            })
            
        except Exception as e:
            # Classification failure handling
            company_data.saas_classification = "Unclassified"
            company_data.classification_justification = f"Classification failed: {str(e)}"
            progress_logger.log_progress(job_id, "classification_failed", {"error": str(e)})
        
        return company_data
```

## Phase 2: UI Integration & Display (Week 2-3)

### 2.1 Company Cards Enhancement
**File: `templates/index.html`**

```html
<!-- Add to company result cards -->
<div class="classification-badge">
    <span class="saas-indicator ${company.is_saas ? 'saas' : 'non-saas'}">
        ${company.is_saas ? 'SaaS' : 'Non-SaaS'}
    </span>
    <span class="category-tag">${company.saas_classification}</span>
    <span class="confidence-score">${(company.classification_confidence * 100).toFixed(0)}%</span>
</div>
```

**File: `static/css/style.css`**

```css
.classification-badge {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
    flex-wrap: wrap;
}

.saas-indicator {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}

.saas-indicator.saas {
    background: #10b981;
    color: white;
}

.saas-indicator.non-saas {
    background: #6366f1;
    color: white;
}

.category-tag {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
}

.confidence-score {
    background: rgba(34, 197, 94, 0.1);
    color: #22c55e;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
}
```

### 2.2 Research Modal Enhancement
**File: `static/js/app.js`**

```javascript
function renderClassificationSection(company) {
    return `
        <div class="research-section">
            <h4>🏷️ Business Model Classification</h4>
            <div class="classification-details">
                <div class="classification-row">
                    <span class="label">Type:</span>
                    <span class="saas-badge ${company.is_saas ? 'saas' : 'non-saas'}">
                        ${company.is_saas ? 'SaaS' : 'Non-SaaS'}
                    </span>
                </div>
                <div class="classification-row">
                    <span class="label">Category:</span>
                    <span class="category">${company.saas_classification || 'Not classified'}</span>
                </div>
                <div class="classification-row">
                    <span class="label">Confidence:</span>
                    <span class="confidence">${company.classification_confidence ? (company.classification_confidence * 100).toFixed(1) + '%' : 'N/A'}</span>
                </div>
                <div class="classification-row">
                    <span class="label">Justification:</span>
                    <span class="justification">${company.classification_justification || 'No justification available'}</span>
                </div>
                <div class="classification-row">
                    <span class="label">Classified:</span>
                    <span class="timestamp">${company.classification_timestamp ? new Date(company.classification_timestamp).toLocaleDateString() : 'N/A'}</span>
                </div>
            </div>
        </div>
    `;
}

// Update renderCompanyDetails to include classification
function renderCompanyDetails(company) {
    return `
        ${renderBasicInformation(company)}
        ${renderBusinessDetails(company)}
        ${renderClassificationSection(company)}
        ${renderTechnologyInformation(company)}
        ${renderResearchMetadata(company)}
    `;
}
```

### 2.3 Filtering & Search Enhancement
**File: `templates/index.html`**

```html
<!-- Add to discovery tab filters -->
<div class="filter-group">
    <label>Business Model Type</label>
    <select id="business-model-filter">
        <option value="">All Companies</option>
        <option value="saas">SaaS Only</option>
        <option value="non-saas">Non-SaaS Only</option>
    </select>
</div>

<div class="filter-group">
    <label>SaaS Category</label>
    <select id="saas-category-filter">
        <option value="">All Categories</option>
        <optgroup label="SaaS Verticals">
            <option value="AdTech">AdTech</option>
            <option value="AssetManagement">Asset Management</option>
            <!-- ... all SaaS categories ... -->
        </optgroup>
        <optgroup label="Non-SaaS Categories">
            <option value="Advertising & Media Services">Advertising & Media Services</option>
            <!-- ... all Non-SaaS categories ... -->
        </optgroup>
    </select>
</div>
```

## Phase 3: API & Export Integration (Week 3-4)

### 3.1 API Endpoint Updates
**File: `app.py`**

```python
@app.route('/api/companies')
def get_companies():
    """Enhanced to include classification filters"""
    business_model = request.args.get('business_model')  # 'saas', 'non-saas'
    category = request.args.get('category')
    
    # Apply filters to Pinecone query
    filter_conditions = {}
    if business_model:
        filter_conditions['is_saas'] = business_model == 'saas'
    if category:
        filter_conditions['saas_classification'] = category
    
    # Query with filters
    companies = pipeline.pinecone_client.query_with_filters(filter_conditions)
    return jsonify(companies)

@app.route('/api/classification/statistics')
def get_classification_stats():
    """Get classification distribution statistics"""
    stats = pipeline.pinecone_client.get_classification_statistics()
    return jsonify(stats)

@app.route('/api/export/classification-csv')
def export_classification_csv():
    """Export companies with classification in required CSV format"""
    companies = pipeline.pinecone_client.get_all_companies()
    
    csv_data = "Company Name;URL;Classification;Justification\n"
    for company in companies:
        csv_data += f"{company.name};{company.website};"
        csv_data += f"{company.saas_classification};{company.classification_justification}\n"
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=theodore_classifications.csv'}
    )
```

### 3.2 Google Sheets Integration
**File: `src/sheets_integration/google_sheets_service_client.py`**

```python
def update_company_classification(self, spreadsheet_id: str, row: int, classification: ClassificationResult):
    """Update classification fields in Google Sheets"""
    
    # Add classification columns to sheets
    classification_data = [
        classification.category.value,
        str(classification.confidence),
        classification.justification,
        "SaaS" if classification.is_saas else "Non-SaaS"
    ]
    
    # Update specific columns for classification
    range_name = f"Companies!F{row}:I{row}"  # Assuming columns F-I for classification
    self._update_sheet_range(spreadsheet_id, range_name, [classification_data])

def setup_classification_headers(self, spreadsheet_id: str):
    """Add classification headers to Google Sheets"""
    headers = ["Classification", "Confidence", "Justification", "Type"]
    # Add to existing headers
```

## Phase 4: Batch Processing & Retroactive Classification (Week 4-5)

### 4.1 Retroactive Classification Script
**File: `scripts/classification/classify_existing_database.py`**

```python
#!/usr/bin/env python3
"""
Classify all existing companies in Theodore database
"""

def classify_existing_companies():
    """Batch classify all companies without classification"""
    
    # Get all companies from Pinecone
    all_companies = pinecone_client.get_all_companies()
    unclassified = [c for c in all_companies if not c.saas_classification]
    
    print(f"Found {len(unclassified)} companies needing classification")
    
    successful = 0
    failed = 0
    
    for i, company in enumerate(unclassified):
        try:
            print(f"Classifying {i+1}/{len(unclassified)}: {company.name}")
            
            classification = classifier.classify_company(company)
            
            # Update in Pinecone
            pinecone_client.update_classification(company.id, classification)
            
            successful += 1
            print(f"  ✅ {classification.category.value} ({classification.confidence:.2f})")
            
        except Exception as e:
            failed += 1
            print(f"  ❌ Failed: {e}")
        
        # Rate limiting
        time.sleep(1)
    
    print(f"\nClassification complete: {successful} successful, {failed} failed")

if __name__ == "__main__":
    classify_existing_companies()
```

### 4.2 Batch Processing Integration
**File: `scripts/batch/batch_process_google_sheet.py`**

```python
# Update batch processing to include classification results
def process_company_with_classification(company_data):
    """Enhanced batch processing with classification"""
    
    result = pipeline.process_single_company(
        company_data['name'], 
        company_data.get('website', '')
    )
    
    # Update Google Sheets with classification
    if result and result.saas_classification:
        sheets_client.update_company_classification(
            TEST_SHEET_ID,
            company_data.get('row', 1),
            ClassificationResult(
                category=SaaSCategory(result.saas_classification),
                confidence=result.classification_confidence,
                justification=result.classification_justification,
                is_saas=result.is_saas
            )
        )
    
    return result
```

## Phase 5: Monitoring & Optimization (Week 5-6)

### 5.1 Classification Analytics
**File: `src/analytics/classification_analytics.py`**

```python
class ClassificationAnalytics:
    def get_classification_distribution(self):
        """Get distribution of classifications"""
        
    def get_confidence_distribution(self):
        """Analyze confidence score distribution"""
        
    def get_saas_vs_non_saas_ratio(self):
        """Get SaaS vs Non-SaaS ratio"""
        
    def identify_low_confidence_classifications(self):
        """Find classifications that may need review"""
```

### 5.2 Settings Dashboard Integration
**File: `templates/settings.html`**

```javascript
function renderClassificationSettings() {
    return `
        <div class="settings-card">
            <div class="card-header">
                <span class="card-icon">🏷️</span>
                <h3 class="card-title">Classification System</h3>
            </div>
            
            <div class="setting-item">
                <label class="setting-label">Classification Status</label>
                <div class="model-status">
                    <span class="status-dot active"></span>
                    <div class="setting-value">Active - 59 Categories</div>
                </div>
            </div>
            
            <div class="setting-item">
                <label class="setting-label">Database Coverage</label>
                <div class="setting-value">${classificationStats.coverage_percentage}% classified</div>
            </div>
            
            <div class="setting-item">
                <label class="setting-label">SaaS vs Non-SaaS Ratio</label>
                <div class="setting-value">${classificationStats.saas_ratio}% SaaS</div>
            </div>
            
            <button class="action-button" onclick="reclassifyDatabase()">Reclassify All</button>
            <button class="action-button" onclick="exportClassifications()">Export CSV</button>
        </div>
    `;
}
```

## Phase 6: Testing & Quality Assurance (Week 6)

### 6.1 Unit Tests
**File: `tests/test_classification.py`**

```python
class TestSaaSClassifier:
    def test_saas_classification(self):
        """Test SaaS company classification"""
        
    def test_non_saas_classification(self):
        """Test Non-SaaS company classification"""
        
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        
    def test_confidence_scores(self):
        """Test confidence score accuracy"""
```

### 6.2 Integration Tests
**File: `tests/test_classification_integration.py`**

```python
class TestClassificationIntegration:
    def test_pipeline_integration(self):
        """Test classification in full pipeline"""
        
    def test_ui_integration(self):
        """Test classification display in UI"""
        
    def test_export_integration(self):
        """Test CSV export functionality"""
```

## Implementation Checklist

### Week 1-2: Foundation
- [ ] Update CompanyData model with classification fields
- [ ] Create SaaSCategory enum with all 59 categories
- [ ] Implement SaaSBusinessModelClassifier class
- [ ] Create classification prompt templates
- [ ] Add Phase 5 to main pipeline
- [ ] Database schema migration script
- [ ] Basic error handling for classification failures

### Week 2-3: UI Integration
- [ ] Add classification badges to company cards
- [ ] Enhance research modal with classification section
- [ ] Add business model and category filters
- [ ] Update CSS for classification styling
- [ ] Implement filtering logic in JavaScript
- [ ] Test UI responsiveness and accessibility

### Week 3-4: API & Export
- [ ] Update API endpoints with classification filters
- [ ] Create classification statistics endpoint
- [ ] Implement CSV export with semicolon delimiters
- [ ] Enhance Google Sheets integration
- [ ] Add classification columns to sheets
- [ ] Test export functionality

### Week 4-5: Batch Processing
- [ ] Create retroactive classification script
- [ ] Update batch processing with classification
- [ ] Test large-scale classification performance
- [ ] Implement progress tracking for batch classification
- [ ] Error recovery for failed classifications

### Week 5-6: Monitoring & Settings
- [ ] Classification analytics dashboard
- [ ] Settings page integration
- [ ] Performance monitoring
- [ ] Classification accuracy validation
- [ ] Documentation and user guides

### Week 6: Testing & QA
- [ ] Comprehensive unit test suite
- [ ] Integration tests for all components
- [ ] Performance testing with large datasets
- [ ] User acceptance testing
- [ ] Bug fixes and optimizations

## Success Metrics
- **Coverage**: 100% of companies have classification
- **Accuracy**: >90% classification accuracy on manual validation
- **Performance**: <5 second increase in processing time per company
- **User Adoption**: Classification filters used in >50% of searches
- **Export Usage**: CSV export used regularly for business analysis

## Risk Mitigation
- **Classification Failures**: Graceful degradation with "Unclassified" category
- **Performance Impact**: Monitoring and optimization of AI model calls
- **Data Migration**: Careful rollout of database schema changes
- **User Training**: Clear documentation and examples of classification system
- **Model Updates**: Versioning system for classification model improvements