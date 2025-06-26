#!/usr/bin/env python3
"""
Cleanup script to remove test files from root directory
"""
import os
import glob

# Files to remove from root
files_to_remove = [
    'test_*.py',
    'framework_integration_plan.md',
    'debug_progress_logging.py'
]

root_dir = '/Users/antoinedubuc/Desktop/AI_Goodies/Theodore'

for pattern in files_to_remove:
    for file_path in glob.glob(os.path.join(root_dir, pattern)):
        try:
            os.remove(file_path)
            print(f"Removed: {file_path}")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

print("Root directory cleanup complete!")