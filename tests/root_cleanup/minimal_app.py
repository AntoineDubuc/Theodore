#!/usr/bin/env python3
"""
Minimal Theodore app to test basic Flask startup
"""

import os
import sys
from flask import Flask, jsonify

# Set up environment
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

# Create minimal Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>🚀 Theodore Minimal Test</h1><p>Basic Flask is working!</p>"

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Minimal Theodore app is running',
        'environment_check': {
            'pinecone_key': bool(os.getenv('PINECONE_API_KEY')),
            'aws_key': bool(os.getenv('AWS_ACCESS_KEY_ID')),
            'gemini_key': bool(os.getenv('GEMINI_API_KEY'))
        }
    })

@app.route('/test-import')
def test_import():
    """Test if we can import Theodore components"""
    results = {}
    
    try:
        from src.models import CompanyIntelligenceConfig
        results['models'] = "✅ OK"
    except Exception as e:
        results['models'] = f"❌ {str(e)}"
    
    try:
        from src.main_pipeline import TheodoreIntelligencePipeline
        results['pipeline'] = "✅ OK"
    except Exception as e:
        results['pipeline'] = f"❌ {str(e)}"
    
    try:
        from src.bedrock_client import BedrockClient
        results['bedrock'] = "✅ OK"
    except Exception as e:
        results['bedrock'] = f"❌ {str(e)}"
    
    return jsonify({
        'import_test': results,
        'message': 'Import test completed'
    })

if __name__ == '__main__':
    print("🧪 Starting MINIMAL Theodore app...")
    print("🌐 Access at: http://localhost:5002")
    print("🔍 Test endpoints:")
    print("   - http://localhost:5002/ (basic test)")
    print("   - http://localhost:5002/api/health (environment check)")
    print("   - http://localhost:5002/test-import (import test)")
    
    app.run(debug=False, host='0.0.0.0', port=5002)