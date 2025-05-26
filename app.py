"""
Theodore Web UI - Modern Flask Application
Beautiful, gradient-styled interface for company similarity discovery
"""

import os
import json
import asyncio
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Theodore modules
import sys
sys.path.insert(0, 'src')
from main_pipeline import TheodoreIntelligencePipeline, find_company_by_name
from models import CompanyIntelligenceConfig

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'theodore-dev-key-2024')

# Initialize Theodore pipeline
config = CompanyIntelligenceConfig()
pipeline = None

def init_pipeline():
    """Initialize Theodore pipeline"""
    global pipeline
    try:
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        print("✅ Theodore pipeline initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Theodore pipeline: {e}")
        pipeline = None

# Initialize pipeline on startup
init_pipeline()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/discover', methods=['POST'])
def discover_similar():
    """API endpoint for similarity discovery"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        limit = min(int(data.get('limit', 5)), 10)  # Max 10 companies
        
        if not company_name:
            return jsonify({'error': 'Company name is required'}), 400
        
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Run async discovery
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Find company
            company_data = loop.run_until_complete(
                find_company_by_name(pipeline, company_name)
            )
            
            if not company_data:
                return jsonify({
                    'error': f'Company "{company_name}" not found in database',
                    'suggestion': 'Try processing the company first or check the spelling'
                }), 404
            
            # Discover similarities
            similarities = loop.run_until_complete(
                pipeline.similarity_pipeline.discover_and_validate_similar_companies(
                    company_data.id, limit=limit
                )
            )
            
            # Format results
            results = []
            for sim in similarities:
                results.append({
                    'company_name': sim.similar_company_name,
                    'similarity_score': round(sim.similarity_score, 3),
                    'confidence': round(sim.confidence, 3),
                    'relationship_type': sim.relationship_type,
                    'reasoning': sim.reasoning[:2] if sim.reasoning else [],  # Top 2 reasons
                    'discovery_method': sim.discovery_method
                })
            
            return jsonify({
                'success': True,
                'target_company': company_data.name,
                'results': results,
                'total_found': len(results),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({'error': f'Discovery failed: {str(e)}'}), 500

@app.route('/api/process', methods=['POST'])
def process_company():
    """API endpoint for processing a single company"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        website = data.get('website', '').strip()
        
        if not company_name or not website:
            return jsonify({'error': 'Company name and website are required'}), 400
        
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Process company
        result = pipeline.process_single_company(company_name, website)
        
        return jsonify({
            'success': True,
            'company_name': result.name,
            'status': result.scrape_status,
            'industry': result.industry,
            'business_model': result.business_model,
            'summary': result.ai_summary[:200] + '...' if result.ai_summary and len(result.ai_summary) > 200 else result.ai_summary,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/search', methods=['GET'])
def search_companies():
    """API endpoint for searching existing companies"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'results': []})
        
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Simple search implementation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            company_data = loop.run_until_complete(
                find_company_by_name(pipeline, query)
            )
            
            results = []
            if company_data:
                results.append({
                    'name': company_data.name,
                    'website': company_data.website,
                    'industry': company_data.industry,
                    'business_model': company_data.business_model
                })
            
            return jsonify({'results': results})
            
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(app.static_folder, 'favicon.ico')

if __name__ == '__main__':
    print("🚀 Starting Theodore Web UI...")
    print("🌐 Access at: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)