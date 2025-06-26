#!/usr/bin/env python3
import os

files_to_remove = [
    'test_business_model_framework.py',
    'test_concurrent_implementation.py',
    'test_framework_integration.py',
    'test_method_fix.py',
    'test_name_only_workflow.py',
    'framework_integration_plan.md',
    'debug_progress_logging.py',
    'cleanup_root.py'
]

for file in files_to_remove:
    if os.path.exists(file):
        os.remove(file)
        print(f"Removed: {file}")
    else:
        print(f"File not found: {file}")

print("Cleanup completed.")