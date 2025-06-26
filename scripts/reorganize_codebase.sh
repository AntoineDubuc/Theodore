#!/bin/bash

# Theodore Codebase Reorganization Script
# This script safely reorganizes the Theodore codebase for better maintainability

set -e  # Exit on any error

echo "🗂️  Starting Theodore codebase reorganization..."
echo "📍 Working directory: $(pwd)"

# Create backup first
echo "📦 Creating backup..."
cp -r . ../Theodore_backup_$(date +%Y%m%d_%H%M%S)

# Create new directory structure
echo "📁 Creating new directory structure..."

# Create experimental directories in src/
mkdir -p src/experimental
mkdir -p src/legacy

# Create new tests structure  
mkdir -p tests/legacy
mkdir -p tests/sandbox

# Create legacy docs
mkdir -p docs/legacy

# 1. MOVE EXPERIMENTAL SRC FILES
echo "🔬 Moving experimental src files..."

# Move experimental files to src/experimental/
mv src/v2_discovery.py src/experimental/ 2>/dev/null || echo "v2_discovery.py not found"
mv src/v2_research.py src/experimental/ 2>/dev/null || echo "v2_research.py not found"
mv src/enhanced_similarity_discovery.py src/experimental/ 2>/dev/null || echo "enhanced_similarity_discovery.py not found"
mv src/similarity_engine.py src/experimental/ 2>/dev/null || echo "similarity_engine.py not found"
mv src/similarity_pipeline.py src/experimental/ 2>/dev/null || echo "similarity_pipeline.py not found"
mv src/similarity_validator.py src/experimental/ 2>/dev/null || echo "similarity_validator.py not found"
mv src/company_discovery.py src/experimental/ 2>/dev/null || echo "company_discovery.py not found"
mv src/clustering.py src/experimental/ 2>/dev/null || echo "clustering.py not found"
mv src/extraction_improvements.py src/experimental/ 2>/dev/null || echo "extraction_improvements.py not found"
mv src/enhanced_page_selection.py src/experimental/ 2>/dev/null || echo "enhanced_page_selection.py not found"
mv src/crawl4ai_scraper.py src/experimental/ 2>/dev/null || echo "crawl4ai_scraper.py not found"

# Move legacy files to src/legacy/
mv src/job_listings_crawler.py src/legacy/ 2>/dev/null || echo "job_listings_crawler.py not found"
mv src/research_manager.py src/legacy/ 2>/dev/null || echo "research_manager.py not found"
mv src/research_prompts.py src/legacy/ 2>/dev/null || echo "research_prompts.py not found"
mv src/similarity_prompts.py src/legacy/ 2>/dev/null || echo "similarity_prompts.py not found"
mv src/intelligent_url_discovery.py src/legacy/ 2>/dev/null || echo "intelligent_url_discovery.py not found"

# 2. MOVE ROOT FILES
echo "📄 Moving root files..."

# Move experimental root files
mv v2_app.py src/experimental/ 2>/dev/null || echo "v2_app.py not found"
mv reprocessing_summary_report.py scripts/analysis/ 2>/dev/null || echo "reprocessing_summary_report.py not found"
mv resmed_improvement_check.py scripts/analysis/ 2>/dev/null || echo "resmed_improvement_check.py not found"

# 3. REORGANIZE TESTS
echo "🧪 Reorganizing tests..."

# Move active tests from tests/ to tests/ (keep the good ones)
# Move legacy tests to tests/legacy/
find tests/ -name "test_*enhanced*.py" -exec mv {} tests/legacy/ \; 2>/dev/null || true
find tests/ -name "test_*similarity*.py" ! -name "test_similarity_engine.py" -exec mv {} tests/legacy/ \; 2>/dev/null || true
find tests/ -name "test_*v2*.py" -exec mv {} tests/legacy/ \; 2>/dev/null || true
find tests/ -name "test_*debug*.py" -exec mv {} tests/legacy/ \; 2>/dev/null || true
find tests/ -name "test_*batch*.py" -exec mv {} tests/legacy/ \; 2>/dev/null || true
find tests/ -name "test_*msi*.py" -exec mv {} tests/legacy/ \; 2>/dev/null || true
find tests/ -name "test_*connatix*.py" -exec mv {} tests/legacy/ \; 2>/dev/null || true

# Rename testing_sandbox to tests/sandbox
if [ -d "testing_sandbox" ]; then
    echo "📦 Moving testing_sandbox to tests/sandbox..."
    mv testing_sandbox tests/sandbox
fi

# 4. REORGANIZE DOCUMENTATION
echo "📚 Reorganizing documentation..."

# Move legacy docs
mv DEBUGGING_LOG.md docs/legacy/ 2>/dev/null || echo "DEBUGGING_LOG.md not found"
mv FINAL_ENHANCEMENT_SUMMARY.md docs/legacy/ 2>/dev/null || echo "FINAL_ENHANCEMENT_SUMMARY.md not found"
mv STARTUP_GUIDE.md docs/legacy/ 2>/dev/null || echo "STARTUP_GUIDE.md not found"

# 5. CREATE README FILES FOR NEW DIRECTORIES
echo "📝 Creating README files for new directories..."

cat > src/experimental/README.md << 'EOF'
# Experimental Modules

This directory contains experimental implementations that are not currently used by the main application but may be valuable for future development.

## Contents

- **v2_*.py** - Version 2 experimental implementations
- **enhanced_*.py** - Enhanced feature implementations
- **similarity_*.py** - Alternative similarity algorithms
- **clustering.py** - Company clustering experiments

## Usage

These modules are not actively maintained but can be referenced for research and development.
EOF

cat > src/legacy/README.md << 'EOF'
# Legacy Modules

This directory contains legacy implementations that have been replaced by newer, more efficient versions in the core system.

## Contents

- **research_manager.py** - Original research management (replaced by simplified approach)
- **job_listings_crawler.py** - Job listing extraction (not used in current UI)
- **intelligent_url_discovery.py** - URL discovery logic (integrated into intelligent_company_scraper.py)

## Important

These files are kept for reference but should not be imported by the main application.
EOF

cat > tests/legacy/README.md << 'EOF'
# Legacy Tests

This directory contains old test files that are no longer actively maintained but kept for reference.

## Contents

- Tests for experimental features
- Debug scripts and one-off tests  
- Integration tests for removed features

## Note

These tests may not pass with current codebase versions.
EOF

cat > tests/sandbox/README.md << 'EOF'
# Testing Sandbox

This directory contains experimental tests, prototypes, and development sandbox code.

## Contents

- **sheets_integration/** - Google Sheets integration experiments
- **experimental/** - Prototype testing code
- Various debugging and development scripts

## Usage

This is a working area for development and testing. Code here may be unstable.
EOF

# 6. UPDATE IMPORT PATHS (Critical step)
echo "🔧 Creating import path update guidance..."

cat > IMPORT_UPDATES_NEEDED.md << 'EOF'
# Import Path Updates Required

After reorganization, the following import paths need to be updated in any files that reference moved modules:

## Moved to src/experimental/:
- `from src.v2_discovery import` → `from src.experimental.v2_discovery import`
- `from src.enhanced_similarity_discovery import` → `from src.experimental.enhanced_similarity_discovery import`
- `from src.similarity_engine import` → `from src.experimental.similarity_engine import`

## Moved to src/legacy/:
- `from src.research_manager import` → `from src.legacy.research_manager import`
- `from src.research_prompts import` → `from src.legacy.research_prompts import`

## Files that may need updates:
- Check app.py for any imports from moved files
- Check any remaining test files
- Check v2_app.py (now in src/experimental/)

## Action Required:
1. Search for imports: `grep -r "from src\." .`
2. Update any imports that reference moved files
3. Test the main application: `python app.py`
EOF

echo "✅ Reorganization complete!"
echo ""
echo "📋 Next steps:"
echo "1. Review IMPORT_UPDATES_NEEDED.md"
echo "2. Update any broken import paths"
echo "3. Test the main application: python app.py"
echo "4. Verify the core features still work"
echo ""
echo "📁 New structure:"
echo "- Core app files remain in root"
echo "- Experimental code moved to src/experimental/"
echo "- Legacy code moved to src/legacy/" 
echo "- Tests reorganized in tests/"
echo "- Documentation cleaned up in docs/"
echo ""
echo "🎯 The core application should still work with:"
echo "- app.py (main Flask app)"
echo "- src/main_pipeline.py"
echo "- src/models.py"
echo "- src/intelligent_company_scraper.py"
echo "- src/simple_enhanced_discovery.py"
echo "- src/*_client.py files"
echo "- src/progress_logger.py"