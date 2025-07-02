#!/usr/bin/env python3
"""
Test for syntax errors in the app
"""
import ast
import os

print("🔍 CHECKING FOR SYNTAX ERRORS")
print("=" * 40)

files_to_check = [
    'app.py',
    'src/intelligent_company_scraper.py',
    'src/main_pipeline.py'
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        print(f"\n📄 Checking {file_path}...")
        try:
            with open(file_path, 'r') as f:
                source = f.read()
            
            # Parse the AST to check for syntax errors
            ast.parse(source)
            print(f"   ✅ {file_path}: No syntax errors")
            
        except SyntaxError as e:
            print(f"   ❌ {file_path}: SYNTAX ERROR!")
            print(f"      Line {e.lineno}: {e.text}")
            print(f"      Error: {e.msg}")
        except Exception as e:
            print(f"   ❌ {file_path}: Other error: {e}")
    else:
        print(f"   ⚠️  {file_path}: File not found")

print("\n🔍 TESTING SIMPLE IMPORT...")
try:
    import sys
    import os
    
    # Set up path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    sys.path.insert(0, '.')
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment loaded")
    
    # Try importing the app
    import app
    print("✅ App module imported successfully")
    
    # Try getting the Flask app
    flask_app = app.app
    print("✅ Flask app object accessible")
    
    print("\n🎉 NO IMPORT ERRORS FOUND!")
    print("The app should be able to start now.")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()