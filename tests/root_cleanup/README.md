# Root Cleanup Directory

This directory contains test files that were previously in the Theodore root directory.
These files have been moved here to clean up the project structure.

## Files moved from root:

### Core Diagnostic Scripts (Already Moved):
- **check_and_restart.py** - Auto-restart system for Theodore app
- **check_imports.py** - Import verification and environment checking
- **debug_pipeline_init.py** - Pipeline initialization debugging
- **internal_diagnostic.py** - Internal component testing
- **manual_test.py** - Manual pipeline investigation
- **minimal_app.py** - Minimal Flask app for basic testing
- **quick_start_test.py** - Quick startup verification test
- **syntax_test.py** - Syntax error checking script

### Additional Test Files (To Be Removed from Root):
- restart_app_with_fixes.py
- restart_fixed_app.py
- run_diagnostic.py
- standalone_diagnostic.py
- start_app_direct.py
- start_app_safe.py
- start_production.py
- test_api_direct.py
- test_app_import.py
- test_krk_fix.py
- test_lazy_init.py
- test_pipeline_simple.py

### Cleanup Scripts:
- cleanup_root_files.py
- final_root_cleanup.py
- complete_root_cleanup.py (self-destructing)

## Purpose
These files were development/debugging scripts that cluttered the root directory.
They remain available for reference but are now properly organized in the test structure.

## Usage
To run any of these diagnostic scripts from the root directory:
```bash
cd /Users/antoinedubuc/Desktop/AI_Goodies/Theodore
python3 tests/root_cleanup/minimal_app.py
python3 tests/root_cleanup/syntax_test.py
python3 tests/root_cleanup/debug_pipeline_init.py
```

The most useful scripts for troubleshooting:
- **minimal_app.py** - Test basic Flask functionality
- **syntax_test.py** - Check for syntax errors in core files  
- **debug_pipeline_init.py** - Debug pipeline component initialization
- **manual_test.py** - Test pipeline creation outside Flask context