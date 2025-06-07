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
from models import CompanyIntelligenceConfig, CompanySimilarity, CompanyData
from progress_logger import progress_logger, start_company_processing

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

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'pipeline_ready': pipeline is not None,
        'similarity_pipeline_ready': pipeline.similarity_pipeline is not None if pipeline else False,
        'discovery_service_ready': pipeline.similarity_pipeline.discovery_service is not None if pipeline and pipeline.similarity_pipeline else False,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/test-discovery', methods=['POST'])
def test_discovery():
    """Test endpoint for fast AI discovery"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', 'Visterra Inc')
        
        print(f"Testing fast discovery for: {company_name}")
        
        # Test the discovery service directly with timeout
        if not pipeline or not pipeline.similarity_pipeline.discovery_service:
            return jsonify({'error': 'Discovery service not available'}), 500
        
        # Create a test company object
        from src.models import CompanyData
        test_company = CompanyData(
            name=company_name,
            website="https://visterrainc.com",
            industry="Biotechnology",
            business_model="B2B",
            company_description="Biotechnology company focused on developing therapeutic antibodies"
        )
        
        # Test discovery (simple version)
        discovery_result = pipeline.similarity_pipeline.discovery_service.discover_similar_companies(
            test_company, 
            limit=3
        )
        
        # Format results
        suggestions = []
        for suggestion in discovery_result.suggestions:
            suggestions.append({
                'company_name': suggestion.company_name,
                'website_url': suggestion.website_url,
                'reason': suggestion.suggested_reason,
                'confidence': suggestion.confidence_score
            })
        
        return jsonify({
            'success': True,
            'target_company': company_name,
            'discovery_method': 'Fast AI Discovery',
            'suggestions': suggestions,
            'total_found': len(suggestions),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except TimeoutError:
        return jsonify({'error': 'Discovery request timed out after 15 seconds'}), 408
    except Exception as e:
        return jsonify({'error': f'Discovery test failed: {str(e)}'}), 500

@app.route('/api/demo', methods=['POST'])
def demo_discovery():
    """Demo endpoint with mock data for testing UI"""
    data = request.get_json()
    company_name = data.get('company_name', '').strip()
    
    if not company_name:
        return jsonify({'error': 'Company name is required'}), 400
    
    # Mock results for UI testing
    mock_results = [
        {
            'company_name': 'GoDaddy',
            'similarity_score': 0.87,
            'confidence': 0.92,
            'relationship_type': 'Domain Services',
            'reasoning': ['Domain registration services', 'Web hosting platform'],
            'discovery_method': 'AI Analysis'
        },
        {
            'company_name': 'Namecheap',
            'similarity_score': 0.82,
            'confidence': 0.88,
            'relationship_type': 'Domain Registrar',
            'reasoning': ['Domain marketplace', 'Competitive pricing model'],
            'discovery_method': 'AI Analysis'
        },
        {
            'company_name': 'Afternic',
            'similarity_score': 0.75,
            'confidence': 0.83,
            'relationship_type': 'Domain Marketplace',
            'reasoning': ['Domain sales platform', 'Secondary market focus'],
            'discovery_method': 'AI Analysis'
        }
    ]
    
    return jsonify({
        'success': True,
        'target_company': company_name,
        'results': mock_results[:int(data.get('limit', 3))],
        'total_found': len(mock_results),
        'timestamp': datetime.utcnow().isoformat(),
        'demo_mode': True
    })

@app.route('/api/discover', methods=['POST'])
def discover_similar_companies():
    """Find companies similar to the given company using enhanced similarity"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        limit = min(int(data.get('limit', 5)), 20)  # Max 20 results
        
        if not company_name:
            return jsonify({
                "error": "Company name is required",
                "companies": []
            }), 400
        
        # Check if pipeline is available
        if not pipeline:
            return jsonify({
                "error": "Theodore pipeline not available",
                "companies": []
            }), 500
        
        # Get similarity insights using NEW advanced similarity engine
        insights = pipeline.analyze_company_similarity(company_name)
        
        if "error" in insights:
            return jsonify({
                "error": insights["error"],
                "suggestion": insights.get("suggestion", "Try processing the company first or check the spelling"),
                "companies": []
            })
        
        # Format response using new enhanced similarity results
        target_company = insights["target_company"]
        similar_companies = insights.get("similar_companies", [])[:limit]
        recommendations = insights.get("sales_recommendations", [])
        patterns = insights.get("patterns", {})
        
        # Convert to response format that matches the UI expectations
        formatted_results = []
        for company in similar_companies:
            formatted_results.append({
                "company_name": company["company_name"],
                "similarity_score": round(company["similarity_score"], 3),
                "confidence": round(company["confidence"], 3),
                "reasoning": [company["explanation"]] if company.get("explanation") else ["AI Analysis"],
                "relationship_type": "Similar Company",
                "discovery_method": "Enhanced AI Analysis"
            })
        
        response = {
            "success": True,
            "target_company": target_company["name"],
            "results": formatted_results,
            "total_found": len(formatted_results),
            "patterns": patterns,
            "sales_recommendations": recommendations,
            "discovery_method": "Enhanced Similarity Analysis",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Discovery endpoint error: {e}")  # Debug log
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "companies": []
        }), 500

@app.route('/api/database', methods=['GET'])
def browse_database():
    """Browse companies in the database"""
    try:
        # Direct Pinecone connection to avoid pipeline issues
        import pinecone
        from pinecone import Pinecone
        
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        pinecone_index_name = os.getenv('PINECONE_INDEX_NAME')
        
        if not pinecone_api_key or not pinecone_index_name:
            return jsonify({"error": "Pinecone configuration missing"}), 500
        
        # Initialize Pinecone directly
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index(pinecone_index_name)
        
        # Get database stats
        try:
            stats = index.describe_index_stats()
            total_companies = stats.total_vector_count if hasattr(stats, 'total_vector_count') else 0
        except Exception as e:
            print(f"Warning: Failed to get index stats: {e}")
            stats = {}
            total_companies = 0
        
        # Get all companies using raw Pinecone query
        companies = []
        try:
            # Query all vectors with metadata
            query_response = index.query(
                vector=[0.0] * 1536,  # Dummy vector for metadata-only query
                top_k=100,
                include_metadata=True,
                include_values=False
            )
            
            for match in query_response.matches:
                metadata = match.metadata or {}
                company_id = match.id
                
                companies.append({
                    "id": company_id,
                    "name": metadata.get('company_name', metadata.get('name', 'Unknown')),
                    "industry": metadata.get('industry', 'Unknown'),
                    "stage": metadata.get('company_stage', 'Unknown'),
                    "tech_level": metadata.get('tech_sophistication', 'Unknown'),
                    "business_model": metadata.get('business_model_type', metadata.get('business_model', 'Unknown')),
                    "geographic_scope": metadata.get('geographic_scope', 'Unknown'),
                    "website": metadata.get('website', 'Unknown'),
                    "target_market": metadata.get('target_market', 'Unknown'),
                    "company_size": metadata.get('company_size', 'Unknown')
                })
            
            # Update total count from actual results if stats failed
            if total_companies == 0:
                total_companies = len(companies)
                
        except Exception as e:
            print(f"Warning: Failed to get companies: {e}")
            # Return empty list if query fails
            companies = []
        
        return jsonify({
            "total_companies": total_companies,
            "companies": companies,
            "database_stats": {"total_vectors": total_companies},
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Database browse error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Database browse failed: {str(e)}"}), 500

@app.route('/api/database/clear', methods=['POST'])
def clear_database():
    """Clear all companies from database"""
    try:
        if not pipeline:
            return jsonify({"error": "Theodore pipeline not available"}), 500
        
        # Clear the database
        success = pipeline.pinecone_client.clear_all_records()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Database cleared successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({"error": "Failed to clear database"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Clear database failed: {str(e)}"}), 500

@app.route('/api/database/add-sample', methods=['POST'])
def add_sample_companies():
    """Add sample companies with proper similarity features"""
    try:
        if not pipeline:
            return jsonify({"error": "Theodore pipeline not available"}), 500
        
        # Sample companies for testing
        sample_companies = [
            ("OpenAI", "https://openai.com"),
            ("Anthropic", "https://anthropic.com"),
            ("Cloud Geometry", "https://cloudgeometry.io"),
            ("Stripe", "https://stripe.com")
        ]
        
        results = []
        for name, website in sample_companies:
            try:
                # Check if already exists
                existing = pipeline.pinecone_client.find_company_by_name(name)
                if existing:
                    results.append(f"✅ {name} already exists")
                    continue
                
                # Process with new similarity features
                company = pipeline.process_single_company(name, website)
                
                if company and company.embedding:
                    results.append(f"✅ Added {name}")
                else:
                    results.append(f"❌ Failed to add {name}")
                    
            except Exception as e:
                results.append(f"❌ Error adding {name}: {str(e)}")
        
        return jsonify({
            "success": True,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": f"Add sample companies failed: {str(e)}"}), 500

@app.route('/api/process-company', methods=['POST'])
def process_company():
    """Process a company with intelligent scraping and real-time progress tracking"""
    if not pipeline:
        return jsonify({'error': 'Theodore pipeline not initialized'}), 500
    
    data = request.get_json()
    company_name = data.get('company_name', '').strip()
    website = data.get('website', '').strip()
    
    if not company_name or not website:
        return jsonify({'error': 'Company name and website are required'}), 400
    
    try:
        # Start processing with progress tracking
        job_id = start_company_processing(company_name)
        
        # Create company data object
        company_data = CompanyData(
            name=company_name,
            website=website
        )
        
        # Process company with intelligent scraper (includes progress logging)
        result = pipeline.scraper.scrape_company(company_data, job_id)
        
        # Store in Pinecone if successful
        if result.scrape_status == "success" and result.company_description:
            # Generate embeddings for the sales intelligence
            embedding = pipeline.bedrock_client.get_embeddings(result.company_description)
            result.embedding = embedding
            
            # Store in Pinecone
            success = pipeline.pinecone_client.upsert_company(result)
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'company_name': result.name,
                'sales_intelligence': result.company_description,
                'pages_processed': len(result.pages_crawled) if result.pages_crawled else 0,
                'processing_time': result.crawl_duration,
                'stored_in_pinecone': success,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'job_id': job_id,
                'error': result.scrape_error or 'Processing failed',
                'timestamp': datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/search', methods=['GET'])
def search_companies():
    """API endpoint for searching existing companies"""
    try:
        query = request.args.get('q', '').strip().lower()
        
        if not query or len(query) < 2:
            return jsonify({'results': []})
        
        # Smart suggestions based on the query
        smart_suggestions = []
        
        # Known companies that match common queries
        company_database = {
            'visterra': {'name': 'Visterra Inc', 'industry': 'Biotechnology', 'business_model': 'B2B'},
            'godaddy': {'name': 'GoDaddy', 'industry': 'Domain Services', 'business_model': 'B2B'},
            'namecheap': {'name': 'Namecheap', 'industry': 'Domain Registrar', 'business_model': 'B2B'},
            'google': {'name': 'Google', 'industry': 'Technology', 'business_model': 'B2B/B2C'},
            'microsoft': {'name': 'Microsoft', 'industry': 'Technology', 'business_model': 'B2B/B2C'},
            'amazon': {'name': 'Amazon', 'industry': 'E-commerce', 'business_model': 'B2B/B2C'},
            'apple': {'name': 'Apple', 'industry': 'Technology', 'business_model': 'B2C'},
            'meta': {'name': 'Meta', 'industry': 'Social Media', 'business_model': 'B2C'},
            'openai': {'name': 'OpenAI', 'industry': 'AI', 'business_model': 'B2B'},
            'anthropic': {'name': 'Anthropic', 'industry': 'AI', 'business_model': 'B2B'}
        }
        
        # Find matches that start with the query (more restrictive)
        for key, company in company_database.items():
            if key.startswith(query):  # Only show if company name starts with query
                smart_suggestions.append({
                    'name': company['name'],
                    'website': f"https://{key}.com",
                    'industry': company['industry'],
                    'business_model': company['business_model']
                })
                
        # If no exact start matches, then allow contains matches but mark them as secondary
        if not smart_suggestions:
            for key, company in company_database.items():
                if query in key and len(query) >= 3:  # Only for longer queries
                    smart_suggestions.append({
                        'name': company['name'],
                        'website': f"https://{key}.com",
                        'industry': company['industry'],
                        'business_model': company['business_model']
                    })
        
        # Sort suggestions by relevance (exact start matches first)
        smart_suggestions.sort(key=lambda x: (
            not x['name'].lower().startswith(query),  # Exact start matches first
            len(x['name'])  # Shorter names first
        ))
        
        return jsonify({'results': smart_suggestions[:5]})  # Return top 5 matches
            
    except Exception as e:
        print(f"Search API error: {e}")
        return jsonify({'results': []})

@app.route('/api/progress/<job_id>')
def get_progress(job_id):
    """Get real-time progress for a processing job"""
    try:
        progress = progress_logger.get_progress(job_id)
        if not progress:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'success': True,
            'progress': progress
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get progress: {str(e)}'}), 500

@app.route('/api/progress/current')
def get_current_progress():
    """Get progress for currently running job"""
    try:
        progress = progress_logger.get_current_job_progress()
        return jsonify({
            'success': True,
            'progress': progress
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get current progress: {str(e)}'}), 500

@app.route('/api/companies')
def list_companies():
    """List all processed companies with their sales intelligence"""
    if not pipeline:
        return jsonify({
            'success': False,
            'error': 'Theodore pipeline not initialized',
            'companies': [],
            'total': 0
        }), 500
    
    try:
        # Get all companies from Pinecone
        # Note: This is a simplified version - in production you'd implement pagination
        companies = []
        
        # Query Pinecone for all vectors (using a dummy query)
        dummy_embedding = [0.0] * 1536  # Standard embedding size
        results = pipeline.pinecone_client.index.query(
            vector=dummy_embedding,
            top_k=100,  # Adjust as needed
            include_metadata=True
        )
        
        for match in results.matches:
            metadata = match.metadata or {}
            companies.append({
                'id': match.id,
                'name': metadata.get('company_name', 'Unknown'),
                'website': metadata.get('website', ''),
                'industry': metadata.get('industry', ''),
                'business_model': metadata.get('business_model', ''),
                'last_updated': metadata.get('last_updated', ''),
                'has_sales_intelligence': bool(metadata.get('has_description', False) or metadata.get('company_description', ''))
            })
        
        return jsonify({
            'success': True,
            'companies': companies,
            'total': len(companies)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to list companies: {str(e)}',
            'companies': [],
            'total': 0
        }), 500

@app.route('/api/company/<company_id>')
def get_company_details(company_id):
    """Get detailed information for a specific company"""
    if not pipeline:
        return jsonify({'error': 'Theodore pipeline not initialized'}), 500
    
    try:
        # Fetch from Pinecone
        result = pipeline.pinecone_client.index.fetch(ids=[company_id])
        
        if company_id not in result.vectors:
            return jsonify({'error': 'Company not found'}), 404
        
        vector_data = result.vectors[company_id]
        metadata = vector_data.metadata
        
        return jsonify({
            'success': True,
            'company': {
                'id': company_id,
                'name': metadata.get('company_name', 'Unknown'),
                'website': metadata.get('website', ''),
                'sales_intelligence': metadata.get('company_description', ''),
                'industry': metadata.get('industry', ''),
                'business_model': metadata.get('business_model', ''),
                'pages_crawled': metadata.get('pages_crawled', []),
                'processing_time': metadata.get('crawl_duration', 0),
                'last_updated': metadata.get('last_updated', ''),
                'scrape_status': metadata.get('scrape_status', 'unknown')
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get company details: {str(e)}'}), 500

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(app.static_folder, 'favicon.ico')

if __name__ == '__main__':
    print("🚀 Starting Theodore Web UI...")
    print("🌐 Access at: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)