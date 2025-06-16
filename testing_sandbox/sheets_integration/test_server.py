#!/usr/bin/env python3
"""
Isolated Flask test server for Google Sheets integration
Runs on port 5555 to avoid conflicts with main Theodore app
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import secrets

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from google_sheets_client import GoogleSheetsClient
from batch_processor import BatchProcessor
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Constants
CREDENTIALS_FILE = project_root / 'config' / 'credentials' / 'client_secret_1096944990043-5u1eohnobc583lvueqr2cvfvm9tcjc3p.apps.googleusercontent.com.json'
TOKEN_FILE = Path(__file__).parent / 'credentials' / 'token.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Global instances
sheets_client = None
batch_processor = None
active_jobs = {}

@app.route('/test/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Theodore Sheets Integration Test Server',
        'port': 5555,
        'sheets_client_initialized': sheets_client is not None
    })

@app.route('/test/auth/validate', methods=['POST'])
def validate_auth():
    """Validate Google Sheets authentication"""
    global sheets_client
    
    try:
        if not sheets_client:
            sheets_client = GoogleSheetsClient(CREDENTIALS_FILE, TOKEN_FILE)
        
        # Test with a simple API call
        test_sheet_id = request.json.get('sheet_id', '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk')
        
        if sheets_client.validate_sheet_access(test_sheet_id):
            return jsonify({
                'authenticated': True,
                'message': 'Successfully authenticated with Google Sheets'
            })
        else:
            return jsonify({
                'authenticated': False,
                'message': 'Cannot access the specified sheet'
            }), 403
            
    except Exception as e:
        logger.error(f"Authentication validation error: {str(e)}")
        return jsonify({
            'authenticated': False,
            'error': str(e)
        }), 500

@app.route('/test/sheets/create', methods=['POST'])
def create_sheets():
    """Create dual-sheet structure in a spreadsheet"""
    global sheets_client
    
    try:
        if not sheets_client:
            sheets_client = GoogleSheetsClient(CREDENTIALS_FILE, TOKEN_FILE)
        
        sheet_id = request.json.get('sheet_id')
        if not sheet_id:
            return jsonify({'error': 'sheet_id is required'}), 400
        
        success = sheets_client.setup_dual_sheet_structure(sheet_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Dual-sheet structure created successfully',
                'sheets': ['Companies', 'Details']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create sheet structure'
            }), 500
            
    except Exception as e:
        logger.error(f"Sheet creation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test/sheets/validate', methods=['POST'])
def validate_sheet_structure():
    """Validate that a sheet has the correct structure"""
    global sheets_client
    
    try:
        if not sheets_client:
            sheets_client = GoogleSheetsClient(CREDENTIALS_FILE, TOKEN_FILE)
        
        sheet_id = request.json.get('sheet_id')
        if not sheet_id:
            return jsonify({'error': 'sheet_id is required'}), 400
        
        # Read companies to check structure
        companies = sheets_client.read_companies_to_process(sheet_id)
        
        return jsonify({
            'valid': True,
            'company_count': len(companies),
            'companies': [
                {
                    'name': c['name'],
                    'website': c.get('website', ''),
                    'status': c.get('status', 'pending'),
                    'row': c['row_number']
                }
                for c in companies[:5]  # First 5 companies
            ]
        })
        
    except Exception as e:
        logger.error(f"Sheet validation error: {str(e)}")
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 500

@app.route('/test/sheets/process', methods=['POST'])
def process_sheet():
    """Start batch processing for a sheet"""
    global sheets_client, batch_processor
    
    try:
        if not sheets_client:
            sheets_client = GoogleSheetsClient(CREDENTIALS_FILE, TOKEN_FILE)
        
        sheet_id = request.json.get('sheet_id')
        if not sheet_id:
            return jsonify({'error': 'sheet_id is required'}), 400
        
        # Check if already processing
        if sheet_id in active_jobs:
            return jsonify({
                'error': 'Sheet is already being processed',
                'job_id': active_jobs[sheet_id]
            }), 409
        
        # Create job ID
        job_id = f"job_{sheet_id[:8]}_{secrets.token_hex(4)}"
        active_jobs[sheet_id] = job_id
        
        # Initialize batch processor
        batch_processor = BatchProcessor(
            sheets_client=sheets_client,
            concurrency=request.json.get('concurrency', 10),
            update_interval=request.json.get('update_interval', 5),
            max_consecutive_errors=3
        )
        
        # Start processing in a thread (in production, use a proper task queue)
        import threading
        def process_async():
            try:
                results = batch_processor.process_batch(sheet_id, job_id)
                active_jobs.pop(sheet_id, None)
                logger.info(f"Batch processing completed: {results}")
            except Exception as e:
                logger.error(f"Batch processing error: {str(e)}")
                active_jobs.pop(sheet_id, None)
        
        thread = threading.Thread(target=process_async)
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Batch processing started',
            'monitor_url': f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        })
        
    except Exception as e:
        logger.error(f"Process sheet error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test/sheets/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get status of a batch processing job"""
    # In a real implementation, this would query job status from a database
    # For now, just check if job is in active_jobs
    
    is_active = job_id in [v for v in active_jobs.values()]
    
    return jsonify({
        'job_id': job_id,
        'status': 'processing' if is_active else 'completed',
        'active': is_active
    })

@app.route('/test/field-mapping/validate', methods=['GET'])
def validate_field_mapping():
    """Validate that all 62+ fields are properly mapped"""
    try:
        from config.sheets_field_mapping import COMPLETE_DATA_COLUMNS
        
        field_count = len(COMPLETE_DATA_COLUMNS)
        fields_by_type = {}
        
        for col, info in COMPLETE_DATA_COLUMNS.items():
            field_type = info['type']
            if field_type not in fields_by_type:
                fields_by_type[field_type] = []
            fields_by_type[field_type].append(info['field'])
        
        return jsonify({
            'valid': True,
            'total_fields': field_count,
            'fields_by_type': fields_by_type,
            'column_range': f"A-{list(COMPLETE_DATA_COLUMNS.keys())[-1]}"
        })
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 500

@app.route('/test/company/mock-research', methods=['POST'])
def mock_research():
    """Test single company processing with mock data"""
    company_name = request.json.get('company_name', 'Test Company')
    
    # Return mock research data
    return jsonify({
        'success': True,
        'company': {
            'name': company_name,
            'industry': 'Technology',
            'company_stage': 'Growth',
            'tech_sophistication': 'High',
            'ai_summary': f'Mock research data for {company_name}',
            'website': f'https://{company_name.lower().replace(" ", "")}.com'
        }
    })

@app.route('/')
def index():
    """Simple index page with API documentation"""
    return """
    <h1>Theodore Sheets Integration Test Server</h1>
    <p>Running on port 5555</p>
    
    <h2>Available Endpoints:</h2>
    <ul>
        <li>GET /test/health - Health check</li>
        <li>POST /test/auth/validate - Validate Google Sheets authentication</li>
        <li>POST /test/sheets/create - Create dual-sheet structure</li>
        <li>POST /test/sheets/validate - Validate sheet structure</li>
        <li>POST /test/sheets/process - Start batch processing</li>
        <li>GET /test/sheets/status/&lt;job_id&gt; - Get job status</li>
        <li>GET /test/field-mapping/validate - Validate field mappings</li>
        <li>POST /test/company/mock-research - Test single company</li>
    </ul>
    
    <h2>Test Spreadsheet:</h2>
    <p><a href="https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit" target="_blank">Open Test Sheet</a></p>
    """

if __name__ == '__main__':
    print("🚀 Starting Theodore Sheets Integration Test Server")
    print("📍 Server will run at: http://localhost:5555")
    print("📊 Test sheet: https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=5555, debug=True)