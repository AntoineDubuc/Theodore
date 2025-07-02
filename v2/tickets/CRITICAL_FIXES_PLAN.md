# Theodore v2 Critical Fixes Implementation Plan

## Priority 1: Architectural Dependency Fixes (IMMEDIATE)

### Fix 1: Resolve Domain → Infrastructure Dependencies

**Issue**: Use cases depend directly on adapters, violating dependency inversion principle.

**Current (❌ Broken)**:
```
TICKET-010 (Research Use Case) → TICKET-006 (Domain Discovery Adapter)
TICKET-011 (Discover Use Case) → TICKET-012 (Google Search Adapter)
TICKET-025 (Export Use Case) → TICKET-016 (Pinecone Adapter)
```

**Fixed (✅ Correct)**:
```
TICKET-010 → TICKET-007 (Web Scraper Port) + TICKET-008 (AI Provider Port) + TICKET-009 (Vector Storage Port)
TICKET-011 → TICKET-005 (MCP Search Port) + TICKET-008 (AI Provider Port) + TICKET-009 (Vector Storage Port)
TICKET-025 → TICKET-009 (Vector Storage Port) + TICKET-004 (Progress Tracking Port)
```

**Action Required**:
1. Update TICKET-010 dependencies to remove TICKET-006
2. Update TICKET-011 dependencies to remove TICKET-012
3. Update TICKET-025 dependencies to remove TICKET-016, TICKET-019

### Fix 2: Create Missing Port Dependencies for Adapters

**Issue**: Adapters don't depend on their interface definitions.

**Required Dependencies**:
```
TICKET-006 (Domain Discovery) → NEW: Domain Discovery Port
TICKET-012 (Google Search) → TICKET-005 (MCP Search Port) 
TICKET-013 (Crawl4AI) → TICKET-007 (Web Scraper Port)
TICKET-014 (Bedrock) → TICKET-008 (AI Provider Port)
TICKET-015 (Gemini) → TICKET-008 (AI Provider Port)
TICKET-016 (Pinecone) → TICKET-009 (Vector Storage Port)
TICKET-017 (Perplexity) → TICKET-005 (MCP Search Port)
TICKET-018 (Tavily) → TICKET-005 (MCP Search Port)
```

### Fix 3: Resolve Interface Duplication

**Issue**: Multiple tickets define the same interfaces.

**Conflicts to Resolve**:
1. **MCPSearchToolPort**: TICKET-017 vs TICKET-018
   - **Solution**: Keep in TICKET-005 (MCP Search Droid Support)
   - Remove from TICKET-017 and TICKET-018

2. **AIProvider + EmbeddingProvider**: TICKET-008 vs TICKET-014
   - **Solution**: Keep in TICKET-008 (AI Provider Port)
   - Remove from TICKET-014

3. **WebScraper**: TICKET-007 vs TICKET-013
   - **Solution**: Keep in TICKET-007 (Scraper Port Interface)
   - Remove from TICKET-013

## Priority 2: Circular Dependency Resolution

### Fix 4: Break Circular Dependencies

**Major Cycles Detected**:
1. **DI Container Cycle**: TICKET-019 ↔ TICKET-025 ↔ TICKET-27
2. **Logging Cycle**: TICKET-015 → TICKET-026 → [multiple] → TICKET-015

**Solution Strategy**:
1. **Remove Future Dependencies**: Adapters should not depend on monitoring (Phase 5)
2. **Defer Non-Critical Dependencies**: Export and logging are not core architecture
3. **Simplify DI Container**: Remove complex cross-dependencies

**Specific Changes**:
```
TICKET-015 (Gemini): Remove TICKET-026 dependency
TICKET-025 (Export): Remove TICKET-019 dependency (optional feature)
TICKET-027 (Integration Tests): Depend only on core components
```

## Priority 3: Complete Missing Specifications

### Fix 5: Complete TICKET-019 (Dependency Injection)

**Missing Elements**:
- File specifications
- Test file specifications  
- Time estimates

**Required Files**:
```python
# Core DI Container Implementation
v2/src/infrastructure/container/container.py
v2/src/infrastructure/container/providers/domain_providers.py
v2/src/infrastructure/container/providers/infrastructure_providers.py
v2/src/infrastructure/container/providers/configuration_providers.py

# Configuration Support
v2/src/infrastructure/container/config/environments/dev.yml
v2/src/infrastructure/container/config/environments/test.yml
v2/src/infrastructure/container/config/environments/prod.yml

# Factory and Lifecycle
v2/src/infrastructure/container/factory.py
v2/src/infrastructure/container/lifecycle.py

# Tests
v2/tests/unit/infrastructure/test_container.py
v2/tests/integration/test_container_integration.py
```

### Fix 6: Complete TICKET-025 (Export Functionality)

**Missing Elements**:
- Time estimate
- Complete file specifications
- Test files

**Required Files**:
```python
# Core Export Implementation  
v2/src/core/use_cases/export_data.py
v2/src/core/domain/value_objects/export_config.py
v2/src/core/domain/value_objects/export_result.py

# Export Formats
v2/src/infrastructure/adapters/export/json_exporter.py
v2/src/infrastructure/adapters/export/csv_exporter.py
v2/src/infrastructure/adapters/export/excel_exporter.py

# Tests
v2/tests/unit/use_cases/test_export_data.py
v2/tests/integration/test_export_integration.py
```

### Fix 7: Complete TICKET-027 (Integration Tests)

**Missing Elements**:
- File specifications
- Time estimate
- Test scenarios

**Required Files**:
```python
# End-to-End Integration Tests
v2/tests/integration/test_research_pipeline.py
v2/tests/integration/test_discovery_pipeline.py
v2/tests/integration/test_export_pipeline.py

# Component Integration Tests
v2/tests/integration/test_adapter_integration.py
v2/tests/integration/test_use_case_integration.py

# Test Utilities
v2/tests/integration/fixtures/test_companies.py
v2/tests/integration/utils/test_helpers.py
```

## Priority 4: Add Missing Port Definitions

### Fix 8: Create Domain Discovery Port

**Issue**: TICKET-006 (Domain Discovery Adapter) has no corresponding port.

**Solution**: Create TICKET-006A (Domain Discovery Port)

**Required Files**:
```python
v2/src/core/ports/domain_discovery.py
v2/tests/unit/ports/test_domain_discovery_mock.py
```

**Dependencies**: TICKET-001 (Core Domain Models)

## Implementation Schedule

### Day 1 Morning: Critical Architecture Fixes
- [ ] Fix 1: Update dependency specifications in tickets 10, 11, 25
- [ ] Fix 2: Add port dependencies to adapter tickets
- [ ] Fix 3: Resolve interface duplication conflicts

### Day 1 Afternoon: Dependency Resolution  
- [ ] Fix 4: Break circular dependencies
- [ ] Validate dependency graph is acyclic
- [ ] Ensure proper phase ordering

### Day 2 Morning: Complete Specifications
- [ ] Fix 5: Complete TICKET-019 specifications
- [ ] Fix 6: Complete TICKET-025 specifications  
- [ ] Fix 7: Complete TICKET-027 specifications

### Day 2 Afternoon: Validation and Testing
- [ ] Fix 8: Add missing port definitions
- [ ] Re-run validation analysis
- [ ] Confirm readiness score > 80/100

## Validation Checkpoints

### After Each Fix
```bash
python3 ticket_validation_analysis.py
```

### Success Criteria
- ✅ Zero circular dependencies
- ✅ All adapters depend on ports
- ✅ All use cases depend only on ports
- ✅ No interface duplication
- ✅ Complete file specifications
- ✅ Readiness score > 80/100

## Risk Mitigation

### Change Management
- **Document all changes** in ticket update log
- **Preserve original tickets** as backup
- **Incremental validation** after each fix

### Quality Assurance
- **Peer review** of architectural changes
- **Interface compatibility** validation
- **Implementation feasibility** review

## Expected Outcome

**After Fixes**:
- **Readiness Score**: 85-95/100
- **Architecture**: Clean hexagonal with proper DDD
- **Dependencies**: Acyclic graph with proper phase ordering
- **Implementation**: Ready for development start

**Timeline**: 2 days of focused architectural fixes will transform the tickets from **CRITICAL** to **IMPLEMENTATION READY**.

---

*This plan addresses the root causes identified in the comprehensive validation analysis and provides a clear path to implementation readiness.*