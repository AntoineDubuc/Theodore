"""
Theodore Web UI - Modern Flask Application
Beautiful, gradient-styled interface for company similarity discovery
"""

import os
import json
import asyncio
import logging
import traceback
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Theodore modules
import sys
sys.path.insert(0, '.')
from src.main_pipeline import TheodoreIntelligencePipeline, find_company_by_name
from src.models import CompanyIntelligenceConfig, CompanySimilarity, CompanyData
from typing import Optional
from src.progress_logger import progress_logger, start_company_processing

# Import authentication modules
from src.auth_manager import AuthManager
from src.auth_routes import auth_bp
from src.auth_decorators import optional_auth, api_auth_optional

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'theodore-dev-key-2024')

# Initialize authentication
auth_manager = AuthManager()
pinecone_api_key = os.getenv('PINECONE_API_KEY')
if pinecone_api_key:
    auth_manager.init_app(app, pinecone_api_key)
    print("✅ Authentication system initialized")
else:
    print("⚠️ Warning: No Pinecone API key found - authentication disabled")

# Register authentication blueprint
app.register_blueprint(auth_bp)

# Initialize Theodore pipeline with robust error handling
config = None
pipeline = None

def get_pipeline():
    """Get or create pipeline instance with detailed component-by-component diagnostics"""
    global pipeline, config
    
    if pipeline is not None:
        return pipeline
    
    print("🔧 DIAGNOSTIC MODE: Testing each pipeline component individually...")
    
    # Store detailed error info for web response
    global last_pipeline_error
    last_pipeline_error = {
        'stage': 'unknown',
        'error': 'Unknown error',
        'component_status': {},
        'env_vars': {}
    }
    
    try:
        # Stage 1: Environment Variables
        print("🔍 Stage 1: Checking environment variables...")
        last_pipeline_error['stage'] = 'environment_check'
        
        env_vars = {
            'PINECONE_API_KEY': os.getenv('PINECONE_API_KEY'),
            'PINECONE_INDEX_NAME': os.getenv('PINECONE_INDEX_NAME'),
            'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY')
        }
        
        for key, value in env_vars.items():
            status = '✅ Set' if value else '❌ Missing'
            print(f"   {key}: {status}")
            last_pipeline_error['env_vars'][key] = bool(value)
        
        if not env_vars['PINECONE_API_KEY']:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        if not env_vars['PINECONE_INDEX_NAME']:
            raise ValueError("PINECONE_INDEX_NAME environment variable not set")
        
        # Stage 2: Config Creation
        print("🔍 Stage 2: Creating config...")
        last_pipeline_error['stage'] = 'config_creation'
        if config is None:
            config = CompanyIntelligenceConfig()
        print("✅ Config created successfully")
        last_pipeline_error['component_status']['config'] = True
        
        # Stage 3: Test Individual Components
        print("🔍 Stage 3: Testing individual components...")
        
        # Test BedrockClient
        print("   Testing BedrockClient...")
        last_pipeline_error['stage'] = 'bedrock_client'
        try:
            from src.bedrock_client import BedrockClient
            bedrock_client = BedrockClient(config)
            print("   ✅ BedrockClient created")
            last_pipeline_error['component_status']['bedrock'] = True
        except Exception as e:
            print(f"   ❌ BedrockClient failed: {e}")
            last_pipeline_error['component_status']['bedrock'] = str(e)
            
        # Test GeminiClient  
        print("   Testing GeminiClient...")
        last_pipeline_error['stage'] = 'gemini_client'
        try:
            from src.gemini_client import GeminiClient
            gemini_client = GeminiClient(config)
            print("   ✅ GeminiClient created")
            last_pipeline_error['component_status']['gemini'] = True
        except Exception as e:
            print(f"   ❌ GeminiClient failed: {e}")
            last_pipeline_error['component_status']['gemini'] = str(e)
            
        # Test PineconeClient
        print("   Testing PineconeClient...")
        last_pipeline_error['stage'] = 'pinecone_client'
        try:
            from src.pinecone_client import PineconeClient
            pinecone_client = PineconeClient(
                config, 
                env_vars['PINECONE_API_KEY'], 
                os.getenv('PINECONE_ENVIRONMENT'),
                env_vars['PINECONE_INDEX_NAME']
            )
            print("   ✅ PineconeClient created")
            last_pipeline_error['component_status']['pinecone'] = True
        except Exception as e:
            print(f"   ❌ PineconeClient failed: {e}")
            last_pipeline_error['component_status']['pinecone'] = str(e)
        
        # Stage 4: Full Pipeline Creation
        print("🔍 Stage 4: Creating full pipeline...")
        last_pipeline_error['stage'] = 'full_pipeline'
        
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=env_vars['PINECONE_API_KEY'],
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=env_vars['PINECONE_INDEX_NAME']
        )
        
        print("✅ FULL PIPELINE CREATED SUCCESSFULLY!")
        last_pipeline_error = None  # Clear error since we succeeded
        return pipeline
        
    except Exception as e:
        error_msg = f"Failed at stage '{last_pipeline_error['stage']}': {str(e)}"
        print(f"❌ {error_msg}")
        
        last_pipeline_error['error'] = str(e)
        try:
            last_pipeline_error['full_traceback'] = traceback.format_exc()
        except:
            last_pipeline_error['full_traceback'] = f"Error details: {str(e)}"
        
        traceback.print_exc()
        pipeline = None
        return None

# Global variable to store last pipeline error for web responses
last_pipeline_error = None

def init_pipeline():
    """Initialize pipeline at startup with error handling"""
    global pipeline
    try:
        pipeline = get_pipeline()
        if pipeline:
            print("✅ Startup pipeline initialization successful")
        else:
            print("❌ Startup pipeline initialization failed - will retry on first request")
    except Exception as e:
        print(f"❌ Startup pipeline initialization crashed: {e}")
        print("⚠️  App will continue without pipeline - will retry on first request")
        pipeline = None

# Initialize pipeline on startup (non-blocking)
try:
    init_pipeline()
except Exception as e:
    print(f"⚠️  Pipeline initialization error during startup: {e}")
    pipeline = None
    print("🔧 App starting anyway - pipeline will be initialized on first request")

@app.route('/')
@optional_auth
def index():
    """Main dashboard page"""
    import time
    from flask_login import current_user
    return render_template('index.html', 
                         timestamp=int(time.time()),
                         current_user=current_user)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    current_pipeline = get_pipeline()
    return jsonify({
        'status': 'healthy',
        'pipeline_ready': current_pipeline is not None,
        'concurrent_scraper_ready': hasattr(current_pipeline, 'scraper') and current_pipeline.scraper is not None if current_pipeline else False,
        'gemini_client_ready': hasattr(current_pipeline, 'gemini_client') and current_pipeline.gemini_client is not None if current_pipeline else False,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/diagnostic')
def diagnostic_check():
    """Detailed diagnostic endpoint to troubleshoot pipeline initialization"""
    global last_pipeline_error
    
    # Force a fresh pipeline check
    current_pipeline = get_pipeline()
    
    response = {
        'pipeline_status': 'success' if current_pipeline else 'failed',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if current_pipeline:
        response.update({
            'message': 'Pipeline initialized successfully!',
            'pipeline_type': str(type(current_pipeline)),
            'components': {
                'scraper': hasattr(current_pipeline, 'scraper') and current_pipeline.scraper is not None,
                'bedrock_client': hasattr(current_pipeline, 'bedrock_client') and current_pipeline.bedrock_client is not None,
                'gemini_client': hasattr(current_pipeline, 'gemini_client') and current_pipeline.gemini_client is not None,
                'pinecone_client': hasattr(current_pipeline, 'pinecone_client') and current_pipeline.pinecone_client is not None
            }
        })
    else:
        response.update({
            'message': 'Pipeline initialization failed',
            'error_details': last_pipeline_error if last_pipeline_error else 'No detailed error information available'
        })
    
    return jsonify(response)

@app.route('/diagnostic')
def diagnostic_page():
    """Diagnostic page for troubleshooting pipeline issues"""
    return render_template('diagnostic.html')

@app.route('/api/companies/details')
def get_companies_details():
    """Get detailed company data for spreadsheet view"""
    if not pipeline:
        return jsonify({'error': 'Theodore pipeline not initialized'}), 500
    
    try:
        # Query all vectors
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=50,
            include_metadata=True,
            include_values=False
        )
        
        companies_with_details = []
        
        for match in query_result.matches:
            metadata = match.metadata
            
            # Extract products/services data
            products_services = metadata.get('products_services_offered', '')
            if isinstance(products_services, str) and products_services:
                products_list = [item.strip() for item in products_services.split(',') if item.strip()]
            else:
                products_list = []
            
            company_detail = {
                'id': match.id,
                'name': metadata.get('company_name', 'Unknown'),
                'website': metadata.get('website', ''),
                'industry': metadata.get('industry', 'Unknown'),
                'products_services_offered': products_list,
                'products_services_text': ', '.join(products_list) if products_list else 'No data',
                'value_proposition': metadata.get('value_proposition', 'No data'),
                'company_culture': metadata.get('company_culture', 'No data'),
                'location': metadata.get('location', 'Unknown'),
                'leadership_team': metadata.get('leadership_team', '').split(',') if metadata.get('leadership_team') else [],
                'job_listings_count': metadata.get('job_listings_count', 0),
                'founding_year': metadata.get('founding_year', 'Unknown'),
                'funding_status': metadata.get('funding_status', 'Unknown'),
                'last_updated': metadata.get('last_updated', 'Unknown'),
                # Token usage and cost data
                'scraped_urls_count': metadata.get('scraped_urls_count', 0),
                'llm_interactions_count': metadata.get('llm_interactions_count', 0),
                'total_input_tokens': metadata.get('total_input_tokens', 0),
                'total_output_tokens': metadata.get('total_output_tokens', 0),
                'total_cost_usd': metadata.get('total_cost_usd', 0.0),
                'llm_calls_count': metadata.get('llm_calls_count', 0)
            }
            companies_with_details.append(company_detail)
        
        # Sort by company name
        companies_with_details.sort(key=lambda x: x['name'])
        
        # Statistics
        companies_with_products = len([c for c in companies_with_details if c['products_services_offered']])
        companies_with_culture = len([c for c in companies_with_details if c['company_culture'] not in ['No data', 'unknown', '']])
        
        return jsonify({
            'success': True,
            'companies': companies_with_details,
            'total': len(companies_with_details),
            'stats': {
                'companies_with_products': companies_with_products,
                'companies_with_culture': companies_with_culture,
                'enhanced_coverage': round((companies_with_products / len(companies_with_details)) * 100) if companies_with_details else 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get detailed companies: {str(e)}'}), 500

@app.route('/api/test-discovery', methods=['POST'])
def test_discovery():
    """Test endpoint for fast AI discovery"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', 'Visterra Inc')
        
        print(f"Testing fast discovery for: {company_name}")
        
        # Check if pipeline is available
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Use SimpleEnhancedDiscovery (same pattern as main discovery endpoint)
        from src.simple_enhanced_discovery import SimpleEnhancedDiscovery
        
        enhanced_discovery = SimpleEnhancedDiscovery(
            ai_client=pipeline.bedrock_client,
            pinecone_client=pipeline.pinecone_client,
            scraper=pipeline.scraper
        )
        
        # Test discovery (limit to 3 for testing)
        discovery_results = enhanced_discovery.discover_similar_companies(
            company_name=company_name,
            limit=3
        )
        
        # Format results
        suggestions = []
        for company_data in discovery_results:
            suggestions.append({
                'company_name': company_data.get('company_name', ''),
                'website_url': company_data.get('website', ''),
                'reason': company_data.get('similarity_explanation', 'Similar business characteristics'),
                'confidence': company_data.get('similarity_score', 0.0)
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
    """Find companies similar to the given company using enhanced multi-pronged discovery"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        limit = min(int(data.get('limit', 5)), 20)  # Max 20 results
        
        # Extract filter parameters
        business_model_filter = data.get('business_model')  # 'saas' or 'non-saas'
        category_filter = data.get('category')  # specific category name
        
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
        
        # Use simplified enhanced similarity discovery
        try:
            # Import and initialize simple enhanced discovery
            from src.simple_enhanced_discovery import SimpleEnhancedDiscovery
            
            enhanced_discovery = SimpleEnhancedDiscovery(
                ai_client=pipeline.bedrock_client,
                pinecone_client=pipeline.pinecone_client,
                scraper=pipeline.scraper
            )
            
            # Run enhanced discovery (sync)
            enhanced_results = enhanced_discovery.discover_similar_companies(
                company_name=company_name,
                limit=limit
            )
            
            logger.info(f"Discovery returned {len(enhanced_results)} results")
            
            if not enhanced_results:
                return jsonify({
                    "error": f"No similar companies found for '{company_name}'",
                    "suggestion": "Try processing the company first or check if it exists in our database",
                    "companies": [],
                    "results": []
                })
            
            # Skip research manager enhancement for now - use results directly
            # This avoids the data structure mismatch issue
            formatted_results = []
            
            # Format response for UI - work directly with enhanced_results
            for company_data in enhanced_results:
                # Check if company exists in database for classification data
                classification_data = {}
                company_name = company_data.get('company_name', '')
                existing_company = pipeline.pinecone_client.find_company_by_name(company_name)
                
                if existing_company:
                    try:
                        # Fetch classification from Pinecone metadata
                        fetch_result = pipeline.pinecone_client.index.fetch(ids=[existing_company.id])
                        if fetch_result.vectors and existing_company.id in fetch_result.vectors:
                            metadata = fetch_result.vectors[existing_company.id].metadata
                            if metadata:
                                classification_data = {
                                    "saas_classification": metadata.get('saas_classification'),
                                    "classification_confidence": metadata.get('classification_confidence'),
                                    "classification_justification": metadata.get('classification_justification'),
                                    "is_saas": metadata.get('is_saas')
                                }
                    except Exception as e:
                        logger.warning(f"Could not fetch classification for {company_name}: {e}")
                
                formatted_results.append({
                    "company_name": company_data.get('company_name', ''),
                    "website": company_data.get('website', ''),
                    "similarity_score": round(company_data.get('similarity_score', 0.0), 3),
                    "confidence": round(company_data.get('confidence', 0.0), 3),
                    "reasoning": company_data.get('reasoning', []),
                    "relationship_type": company_data.get('relationship_type', 'similar'),
                    "discovery_method": company_data.get('discovery_method', 'Unknown'),
                    "business_context": company_data.get('business_context', ''),
                    "sources": company_data.get('sources', []),
                    "research_status": 'completed' if existing_company else 'unknown',
                    "in_database": bool(existing_company),
                    "database_id": existing_company.id if existing_company else None,
                    **classification_data  # Include classification data if available
                })
            
            # Apply filters to results
            filtered_results = formatted_results
            if business_model_filter or category_filter:
                filtered_results = []
                for result in formatted_results:
                    # Check business model filter
                    if business_model_filter:
                        if business_model_filter == 'saas' and not result.get('is_saas'):
                            continue
                        elif business_model_filter == 'non-saas' and result.get('is_saas'):
                            continue
                    
                    # Check category filter
                    if category_filter and result.get('saas_classification') != category_filter:
                        continue
                    
                    filtered_results.append(result)
            
            response = {
                "success": True,
                "target_company": company_name,
                "results": filtered_results,
                "total_found": len(filtered_results),
                "total_before_filter": len(formatted_results),
                "filters_applied": {
                    "business_model": business_model_filter,
                    "category": category_filter
                } if (business_model_filter or category_filter) else None,
                "discovery_method": "Enhanced Multi-Source Discovery",
                "sources_used": list(set([s for r in enhanced_results for s in r.get("sources", [])])),
                "timestamp": datetime.now().isoformat()
            }
            
            return jsonify(response)
            
        except Exception as discovery_error:
            logger.error(f"Enhanced discovery failed: {discovery_error}")
            import traceback
            traceback.print_exc()
            
            # Fallback to basic similarity analysis
            insights = pipeline.analyze_company_similarity(company_name)
            
            if "error" in insights:
                return jsonify({
                    "error": insights["error"],
                    "suggestion": insights.get("suggestion", "Try processing the company first or check the spelling"),
                    "companies": []
                })
            
            # Format fallback response
            target_company = insights["target_company"]
            similar_companies = insights.get("similar_companies", [])[:limit]
            
            formatted_results = []
            for company in similar_companies:
                formatted_results.append({
                    "company_name": company["company_name"],
                    "similarity_score": round(company["similarity_score"], 3),
                    "confidence": round(company["confidence"], 3),
                    "reasoning": [company["explanation"]] if company.get("explanation") else ["Vector Similarity"],
                    "relationship_type": "Similar Company",
                    "discovery_method": "Basic Vector Similarity (Fallback)"
                })
            
            response = {
                "success": True,
                "target_company": target_company["name"],
                "results": formatted_results,
                "total_found": len(formatted_results),
                "discovery_method": "Basic Similarity Analysis (Fallback)",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return jsonify(response)
        
    except Exception as e:
        print(f"Discovery endpoint error: {e}")  # Debug log
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "companies": []
        }), 500

@app.route('/api/research', methods=['POST'])
@api_auth_optional
def research_company():
    """Research a specific company using AsyncExecutionManager - DIRECT APPROACH"""
    
    try:
        data = request.get_json()
        print(f"🐍 FLASK: ===== RESEARCH ENDPOINT CALLED =====")
        print(f"🐍 FLASK: Request method: {request.method}")
        print(f"🐍 FLASK: Request content type: {request.content_type}")
        
        # Parse request data
        print(f"🐍 FLASK: Attempting to parse JSON request data...")
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        print(f"🐍 FLASK: JSON parsed successfully")
        print(f"🐍 FLASK: Request data keys: {list(data.keys())}")
        print(f"🐍 FLASK: Full request data: {data}")
        
        company_data = data.get('company', {})
        print(f"🐍 FLASK: Company data extracted: {company_data}")
        
        if not company_data or not company_data.get('name'):
            error_response = {
                "error": "Company data is required",
                "company": {}
            }
            return jsonify(error_response), 400
        
        company_name = company_data.get('name')
        company_website = company_data.get('website', '')
        print(f"🐍 FLASK: Company name: {company_name}")
        print(f"🐍 FLASK: Company website: {company_website}")
        
        # Check if pipeline is available
        print(f"🐍 FLASK: Checking pipeline availability...")
        if not pipeline:
            error_response = {
                "error": "Theodore pipeline not available",
                "company": {}
            }
            return jsonify(error_response), 500
        print(f"🐍 FLASK: ✅ Pipeline available, proceeding with research")
        
        # Verify pipeline components
        has_scraper = hasattr(pipeline, 'scraper') and pipeline.scraper is not None
        has_bedrock = hasattr(pipeline, 'bedrock_client') and pipeline.bedrock_client is not None  
        has_pinecone = hasattr(pipeline, 'pinecone_client') and pipeline.pinecone_client is not None
        print(f"🐍 FLASK: Pipeline components: scraper={has_scraper}, bedrock={has_bedrock}, pinecone={has_pinecone}")
        
        print(f"🐍 FLASK: ===== STARTING RESEARCH PROCESS =====")
        print(f"🐍 FLASK: Research target: {company_name}")
        
        try:
            # Use the pipeline's process_single_company method
            print(f"🐍 FLASK: Using pipeline.process_single_company method...")
            from src.progress_logger import start_company_processing
            
            print(f"🐍 FLASK: Step 1 - Starting progress tracking...")
            # Start progress tracking
            job_id = start_company_processing(company_name)
            print(f"🐍 FLASK: ✅ Progress tracking started with job_id: {job_id}")
            
            print(f"🐍 FLASK: Step 2 - Using process_single_company method...")
            print(f"🐍 FLASK: This will use the subprocess approach via IntelligentCompanyScraperSync...")
            
            import time
            start_time = time.time()
            
            # Use the original process_single_company method without signal-based timeout
            # (The scraper has its own built-in timeout handling)
            scraped_company = pipeline.process_single_company(
                company_name,
                company_website,
                job_id=job_id
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"🐍 FLASK: ===== SCRAPING COMPLETED =====")
            print(f"🐍 FLASK: Duration: {duration:.2f} seconds")
            print(f"🐍 FLASK: Result type: {type(scraped_company)}")
            print(f"🐍 FLASK: Company description length: {len(scraped_company.company_description or '') if hasattr(scraped_company, 'company_description') else 'N/A'}")
            
            # Save to Pinecone if scraping was successful
            if scraped_company and hasattr(scraped_company, 'company_description') and scraped_company.company_description:
                print(f"🐍 FLASK: Step 6 - Saving to Pinecone...")
                try:
                    # Generate embedding and save
                    embedding = pipeline.bedrock_client.get_embeddings(scraped_company.company_description)
                    scraped_company.embedding = embedding
                    
                    success = pipeline.pinecone_client.upsert_company(scraped_company)
                    print(f"🐍 FLASK: ✅ Saved to Pinecone: {success}")
                except Exception as save_error:
                    print(f"🐍 FLASK: ⚠️ Failed to save to Pinecone: {save_error}")
            
            # Convert to dict for JSON response
            if hasattr(scraped_company, 'to_dict'):
                company_dict = scraped_company.to_dict()
            else:
                company_dict = scraped_company.__dict__ if hasattr(scraped_company, '__dict__') else {}
            
            success_response = {
                "success": True,
                "company": company_dict,
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time": duration,
                "method": "AsyncExecutionManager",
                "job_id": job_id
            }
            
            print(f"🐍 FLASK: ✅ Sending success response")
            return jsonify(success_response)
            
        except Exception as research_error:
            print(f"🐍 FLASK: ❌ Research failed: {research_error}")
            
            import traceback
            traceback_str = traceback.format_exc()
            print(f"🐍 FLASK: ❌ Full traceback: {traceback_str}")
            
            error_response = {
                "error": f"AsyncExecutionManager research failed: {str(research_error)}",
                "company": company_data,
                "exception_type": type(research_error).__name__,
                "method": "AsyncExecutionManager"
            }
            return jsonify(error_response), 500
            
    except Exception as endpoint_error:
        print(f"🐍 FLASK: ❌ Endpoint error: {endpoint_error}")
        
        import traceback
        traceback_str = traceback.format_exc()
        print(f"🐍 FLASK: ❌ Full endpoint traceback: {traceback_str}")
        
        critical_error_response = {
            "error": f"Internal server error: {str(endpoint_error)}",
            "company": {},
            "exception_type": type(endpoint_error).__name__
        }
        
        return jsonify(critical_error_response), 500

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

@app.route('/batch')
def batch_processing():
    """Batch processing page"""
    return render_template('batch_processing.html')

@app.route('/docs/features/sheets_integration/')
def sheets_integration_docs():
    """Serve Google Sheets integration documentation"""
    try:
        from pathlib import Path
        docs_path = Path('docs/features/sheets_integration/README.md')
        if docs_path.exists():
            with open(docs_path, 'r') as f:
                content = f.read()
            # Simple markdown to HTML conversion for basic display
            html_content = content.replace('\n', '<br>').replace('# ', '<h1>').replace('## ', '<h2>')
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Google Sheets Integration - Theodore Documentation</title>
                <style>
                    body {{ font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }}
                    h1, h2 {{ color: #3b82f6; }}
                    code {{ background: #f3f4f6; padding: 0.25rem 0.5rem; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <div>{html_content}</div>
                <hr>
                <p><a href="/settings">← Back to Settings</a></p>
            </body>
            </html>
            """
        else:
            return "<h1>Documentation not found</h1><p><a href='/settings'>← Back to Settings</a></p>"
    except Exception as e:
        return f"<h1>Error loading documentation</h1><p>{str(e)}</p><p><a href='/settings'>← Back to Settings</a></p>"

@app.route('/api/settings')
def get_settings():
    """Get current system settings and configuration"""
    try:
        # Get current model configuration
        models = {
            'bedrock_model': os.getenv('BEDROCK_ANALYSIS_MODEL', 'amazon.nova-pro-v1:0'),
            'gemini_model': 'gemini-2.5-flash-preview-05-20',
            'openai_model': 'gpt-4o-mini',
            'bedrock_available': bool(os.getenv('AWS_ACCESS_KEY_ID')),
            'gemini_available': bool(os.getenv('GEMINI_API_KEY')),
            'openai_available': bool(os.getenv('OPENAI_API_KEY'))
        }
        
        # Cost estimates
        cost_estimates = {
            'per_company': '0.0045',
            'batch_10': '0.05',
            'batch_100': '0.47',
            'batch_400': '1.89',
            'batch_1000': '4.70',
            'primary_analysis': '0.0042',
            'enhancement_cost': '0.0002',
            'embedding': '0.0001'
        }
        
        # Get prompts from the system
        prompts = {
            'analysis_prompt': get_analysis_prompt(),
            'page_selection_prompt': get_page_selection_prompt()
        }
        
        # System status
        system_status = {
            'pinecone_connected': bool(pipeline and pipeline.pinecone_client),
            'pinecone_index': os.getenv('PINECONE_INDEX_NAME', 'theodore-companies'),
            'companies_count': get_companies_count(),
            'last_processing': 'Recent',
            'uptime': get_system_uptime()
        }
        
        # Extraction settings
        extraction_settings = {
            'timeout': 300,  # 5 minutes for CloudGeometry testing
            'max_pages': 50,
            'enhanced_enabled': True,
            'patterns_count': get_patterns_count()
        }
        
        # Google Sheets integration
        google_sheets = {
            'service_account_configured': check_sheets_service_account(),
            'sheet_url': 'https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit#gid=0',
            'sheet_id': '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk',
            'features_available': [
                'Batch Processing',
                'Progress Tracking', 
                'Error Recovery',
                'Real-time Updates'
            ]
        }
        
        # Performance metrics
        performance = {
            'avg_processing_time': '45',
            'success_rate': '75',
            'field_extraction_rate': '23',
            'companies_processed_24h': '0'
        }
        
        return jsonify({
            'models': models,
            'cost_estimates': cost_estimates,
            'prompts': prompts,
            'system_status': system_status,
            'extraction_settings': extraction_settings,
            'performance': performance,
            'google_sheets': google_sheets
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get settings: {str(e)}"}), 500

@app.route('/api/settings/test-models', methods=['POST'])
def test_models():
    """Test AI model connections"""
    try:
        results = {}
        
        # Test Bedrock
        try:
            if pipeline and pipeline.bedrock_client:
                # Test with a simple embedding call
                test_text = "Test connection"
                embedding = pipeline.bedrock_client.get_embeddings(test_text)
                if embedding and len(embedding) > 0:
                    results['bedrock'] = 'Connected ✅'
                else:
                    results['bedrock'] = 'Connected but no response'
            else:
                results['bedrock'] = 'Not configured'
        except Exception as e:
            results['bedrock'] = f'Error: {str(e)[:100]}'
        
        # Test Gemini
        try:
            if pipeline and pipeline.gemini_client:
                # Test with a minimal prompt
                test_prompt = "Reply with 'OK' if you receive this."
                response = pipeline.gemini_client.generate_text(test_prompt, max_tokens=10)
                if response and 'OK' in str(response):
                    results['gemini'] = 'Connected ✅'
                else:
                    results['gemini'] = 'Connected but unexpected response'
            else:
                results['gemini'] = 'Not configured'
        except Exception as e:
            results['gemini'] = f'Error: {str(e)[:100]}'
        
        # Test OpenAI (if configured)
        try:
            if os.getenv('OPENAI_API_KEY'):
                from src.openai_client import OpenAIClient
                openai_client = OpenAIClient()
                # Simple test
                test_response = openai_client.generate_response("Reply with OK", max_tokens=10)
                if test_response and 'OK' in test_response:
                    results['openai'] = 'Connected ✅'
                else:
                    results['openai'] = 'Connected but unexpected response'
            else:
                results['openai'] = 'Not configured (optional)'
        except Exception as e:
            results['openai'] = f'Error: {str(e)[:100]}'
        
        # Overall status
        all_configured = any('Connected ✅' in str(v) for v in results.values())
        
        return jsonify({
            'success': True,
            'message': 'Model tests completed' + (' - All systems operational!' if all_configured else ''),
            'results': results
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to test models: {str(e)}"}), 500

@app.route('/api/settings/recalculate-costs', methods=['POST'])
def recalculate_costs():
    """Recalculate cost estimates"""
    try:
        # Cost calculation based on current model pricing
        # Nova Pro: $0.80 per million input tokens, $3.20 per million output tokens
        # Gemini Flash: ~$0.05 per million tokens
        # Embeddings: ~$0.10 per million tokens
        
        # Average tokens per company (based on empirical data)
        avg_input_tokens = 25000  # Discovery + selection + crawling
        avg_output_tokens = 8000  # Extraction + analysis
        
        # Calculate costs
        nova_input_cost = (avg_input_tokens / 1_000_000) * 0.80
        nova_output_cost = (avg_output_tokens / 1_000_000) * 3.20
        gemini_cost = (5000 / 1_000_000) * 0.05  # Supplementary analysis
        embedding_cost = (1000 / 1_000_000) * 0.10
        
        total_per_company = nova_input_cost + nova_output_cost + gemini_cost + embedding_cost
        
        updated_estimates = {
            'per_company': f"{total_per_company:.4f}",
            'batch_10': f"{total_per_company * 10:.2f}",
            'batch_100': f"{total_per_company * 100:.2f}",
            'batch_400': f"{total_per_company * 400:.2f}",
            'batch_1000': f"{total_per_company * 1000:.2f}",
            'primary_analysis': f"{nova_input_cost + nova_output_cost:.4f}",
            'enhancement_cost': f"{gemini_cost:.4f}",
            'embedding': f"{embedding_cost:.4f}"
        }
        
        return jsonify({
            'success': True,
            'message': 'Costs recalculated based on current model pricing',
            'updated_estimates': updated_estimates,
            'calculation_details': {
                'avg_input_tokens': avg_input_tokens,
                'avg_output_tokens': avg_output_tokens,
                'nova_pro_rate': '$0.80/$3.20 per million tokens (input/output)',
                'gemini_rate': '$0.05 per million tokens',
                'embedding_rate': '$0.10 per million tokens'
            }
        })
    except Exception as e:
        # Fallback to default estimates
        return jsonify({
            'success': True,
            'message': 'Using default cost estimates',
            'updated_estimates': {
                'per_company': '0.0280',
                'batch_10': '0.28',
                'batch_100': '2.80',
                'batch_400': '11.20',
                'batch_1000': '28.00',
                'primary_analysis': '0.0260',
                'enhancement_cost': '0.0003',
                'embedding': '0.0001'
            },
            'note': f'Calculation error: {str(e)}'
        })

@app.route('/api/settings/save-prompt', methods=['POST'])
def save_prompt():
    """Save updated prompt"""
    try:
        data = request.get_json()
        prompt_type = data.get('type')
        prompt_content = data.get('prompt')
        
        if not prompt_type or not prompt_content:
            return jsonify({"error": "Prompt type and content are required"}), 400
        
        # Save the prompt using the storage system
        storage = get_prompt_storage()
        success = storage.save_prompt(prompt_type, prompt_content)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'{prompt_type.title()} prompt saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save prompt'
            }), 500
            
    except Exception as e:
        return jsonify({"error": f"Failed to save prompt: {str(e)}"}), 500

@app.route('/api/settings/reset-prompts', methods=['POST'])
def reset_prompts():
    """Reset prompts to defaults"""
    try:
        storage = get_prompt_storage()
        storage.reset_all_prompts()
        
        return jsonify({
            'success': True,
            'message': 'All prompts reset to defaults'
        })
    except Exception as e:
        return jsonify({"error": f"Failed to reset prompts: {str(e)}"}), 500

@app.route('/api/settings/reset-single-prompt', methods=['POST'])
def reset_single_prompt():
    """Reset a single prompt to its default value"""
    try:
        data = request.get_json()
        prompt_type = data.get('type')
        
        if not prompt_type:
            return jsonify({"error": "Prompt type is required"}), 400
        
        # Reset the prompt using storage system
        storage = get_prompt_storage()
        
        try:
            default_prompt = storage.reset_prompt(prompt_type)
            return jsonify({
                'success': True,
                'message': f'{prompt_type.replace("_", " ").title()} prompt reset to default',
                'default_prompt': default_prompt
            })
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        return jsonify({"error": f"Failed to reset prompt: {str(e)}"}), 500

@app.route('/api/settings/health-check', methods=['POST'])
def settings_health_check():
    """Perform system health check"""
    try:
        health_results = {}
        
        # Check pipeline
        health_results['pipeline'] = 'Healthy' if pipeline else 'Not initialized'
        
        # Check Pinecone
        try:
            if pipeline and pipeline.pinecone_client:
                # This would be a lightweight check
                health_results['pinecone'] = 'Connected'
            else:
                health_results['pinecone'] = 'Not connected'
        except Exception as e:
            health_results['pinecone'] = f'Error: {str(e)}'
        
        # Check AI models
        health_results['models'] = 'Available' if any([
            os.getenv('AWS_ACCESS_KEY_ID'),
            os.getenv('GEMINI_API_KEY'),
            os.getenv('OPENAI_API_KEY')
        ]) else 'No models configured'
        
        overall_health = 'Healthy' if all(
            status not in ['Not initialized', 'Not connected', 'No models configured']
            for status in health_results.values()
        ) else 'Issues detected'
        
        return jsonify({
            'success': True,
            'message': f'Health check completed: {overall_health}',
            'results': health_results,
            'overall_health': overall_health
        })
        
    except Exception as e:
        return jsonify({"error": f"Health check failed: {str(e)}"}), 500

# Import prompt storage system
from src.prompt_storage import get_prompt_storage

# Helper functions for settings
def get_analysis_prompt():
    """Get the current company analysis prompt"""
    storage = get_prompt_storage()
    return storage.get_prompt('analysis')

def get_page_selection_prompt():
    """Get the current page selection prompt"""
    storage = get_prompt_storage()
    return storage.get_prompt('page_selection')


def get_companies_count():
    """Get count of companies in database"""
    try:
        if pipeline and pipeline.pinecone_client:
            # This would query the actual count from Pinecone
            return "10+"  # Placeholder
        return "0"
    except:
        return "Unknown"

def get_system_uptime():
    """Get system uptime"""
    # This would calculate actual uptime
    return "2h 15m"

def get_patterns_count():
    """Get count of active extraction patterns"""
    # This would count the actual patterns in the extraction system
    return 15

def check_sheets_service_account():
    """Check if Google Sheets service account is configured"""
    try:
        from pathlib import Path
        service_account_file = Path('config/credentials/theodore-service-account.json')
        return service_account_file.exists()
    except Exception:
        return False

@app.route('/api/settings/test-sheets-connection', methods=['POST'])
def test_sheets_connection():
    """Test Google Sheets service account connection"""
    try:
        from pathlib import Path
        
        service_account_file = Path('config/credentials/theodore-service-account.json')
        
        if not service_account_file.exists():
            return jsonify({
                'success': False,
                'message': 'Service account file not found. Check config/credentials/theodore-service-account.json'
            })
        
        # Try to import and test the sheets client
        try:
            from src.sheets_integration import GoogleSheetsServiceClient
            sheets_client = GoogleSheetsServiceClient(service_account_file)
            
            # Test connection by attempting to access the test sheet
            sheet_id = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'
            
            # Simple read test - get sheet metadata
            sheet_info = sheets_client.service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheet_title = sheet_info.get('properties', {}).get('title', 'Unknown')
            
            return jsonify({
                'success': True,
                'message': f'✅ Connected successfully to sheet: "{sheet_title}"'
            })
            
        except ImportError:
            return jsonify({
                'success': False,
                'message': 'Google Sheets integration not available. Missing dependencies.'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Connection failed: {str(e)}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error testing connection: {str(e)}'
        })

@app.route('/api/save-researched-company', methods=['POST'])
def save_researched_company():
    """Save a researched company to the database"""
    try:
        if not pipeline:
            return jsonify({"error": "Theodore pipeline not available"}), 500
        
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        website = data.get('website', '').strip()
        
        if not company_name:
            return jsonify({"error": "Company name is required"}), 400
        
        # Check if company already exists in database
        existing_company = pipeline.pinecone_client.find_company_by_name(company_name)
        if existing_company:
            return jsonify({
                "success": True,
                "message": f"{company_name} already exists in database",
                "company_id": existing_company.id,
                "was_existing": True
            })
        
        # If website is not provided, try to infer it
        if not website:
            website = f"https://{company_name.lower().replace(' ', '').replace('.', '')}.com"
        
        # Process the company (this will scrape, analyze, and store it)
        print(f"Processing and saving {company_name} to database...")
        processed_company = pipeline.process_single_company(company_name, website)
        
        if processed_company and processed_company.embedding:
            return jsonify({
                "success": True,
                "message": f"{company_name} saved to database successfully",
                "company_id": processed_company.id,
                "was_existing": False,
                "scrape_status": processed_company.scrape_status,
                "has_embedding": bool(processed_company.embedding)
            })
        else:
            return jsonify({
                "error": f"Failed to process {company_name}. Scraping may have failed.",
                "scrape_status": processed_company.scrape_status if processed_company else "unknown",
                "scrape_error": processed_company.scrape_error if processed_company else "Unknown error"
            }), 500
            
    except Exception as e:
        print(f"Save researched company error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Failed to save company: {str(e)}"
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

def discover_company_domain(company_name: str) -> Optional[str]:
    """Discover company domain using Google search when no URL provided"""
    try:
        import requests
        from urllib.parse import quote
        
        # Configure SSL handling
        requests.packages.urllib3.disable_warnings()
        
        # Use Google search to find company website
        search_query = f"{company_name} official website"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try DuckDuckGo first (no rate limiting)
        try:
            search_url = f"https://duckduckgo.com/html/?q={quote(search_query)}"
            response = requests.get(search_url, headers=headers, timeout=10, verify=False)
            
            if response.status_code == 200:
                import re
                # Extract URLs from DuckDuckGo results
                url_pattern = r'href="([^"]*)"[^>]*>[^<]*' + re.escape(company_name.split()[0])
                urls = re.findall(url_pattern, response.text, re.IGNORECASE)
                
                for url in urls[:3]:  # Check first 3 results
                    if url.startswith('http') and not any(blocked in url for blocked in ['duckduckgo', 'wikipedia', 'linkedin', 'facebook', 'twitter']):
                        return url
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
        
        # Fallback: construct likely URLs
        company_slug = company_name.lower().replace(' ', '').replace(',', '').replace('.', '')
        potential_domains = [
            f"https://www.{company_slug}.com",
            f"https://{company_slug}.com", 
            f"https://www.{company_slug}.ca",
            f"https://{company_slug}.ca"
        ]
        
        # Test which domain responds
        for domain in potential_domains:
            try:
                test_response = requests.head(domain, timeout=5, allow_redirects=True, verify=False)
                if test_response.status_code < 400:
                    return domain
            except:
                continue
                
        return None
        
    except Exception as e:
        logger.error(f"Error discovering domain for {company_name}: {e}")
        return None

def normalize_website_url(website: str) -> str:
    """Normalize website URL by adding https:// prefix if needed"""
    if not website:
        return website
        
    website = website.strip()
    
    # Add https:// if missing
    if not website.startswith(('http://', 'https://')):
        website = f"https://{website}"
    
    return website

@app.route('/api/process-company', methods=['POST'])
def process_company():
    """Process a company with intelligent scraping and real-time progress tracking"""
    # Robust pipeline retrieval with lazy initialization
    current_pipeline = get_pipeline()
    
    if not current_pipeline:
        # Include detailed diagnostic information in the response
        global last_pipeline_error
        error_response = {
            'error': 'Theodore pipeline initialization failed',
            'suggestion': 'Check the detailed diagnostic information below to identify the issue.',
        }
        
        if last_pipeline_error:
            error_response.update({
                'diagnostic_info': {
                    'failed_stage': last_pipeline_error.get('stage', 'unknown'),
                    'error_message': last_pipeline_error.get('error', 'Unknown error'),
                    'component_status': last_pipeline_error.get('component_status', {}),
                    'environment_variables': last_pipeline_error.get('env_vars', {}),
                    'full_traceback': last_pipeline_error.get('full_traceback', 'Not available')
                }
            })
        else:
            # Fallback diagnostic info
            error_response.update({
                'basic_debug_info': {
                    'pinecone_key_set': bool(os.getenv('PINECONE_API_KEY')),
                    'pinecone_index_set': bool(os.getenv('PINECONE_INDEX_NAME')),
                    'aws_key_set': bool(os.getenv('AWS_ACCESS_KEY_ID')),
                    'gemini_key_set': bool(os.getenv('GEMINI_API_KEY'))
                }
            })
        
        return jsonify(error_response), 500
    
    print(f"✅ PIPELINE STATUS: Pipeline available - {type(current_pipeline)}")
    
    data = request.get_json()
    company_name = data.get('company_name', '').strip()
    website = data.get('website', '').strip()
    
    if not company_name:
        return jsonify({'error': 'Company name is required'}), 400
    
    # If no website provided, try to discover it
    if not website:
        logger.info(f"No website provided for {company_name}, attempting domain discovery...")
        discovered_website = discover_company_domain(company_name)
        if discovered_website:
            website = discovered_website
            logger.info(f"Discovered website for {company_name}: {website}")
        else:
            return jsonify({'error': f'Could not find website for {company_name}. Please provide a website URL.'}), 400
    
    # Normalize the website URL (add https:// if needed)
    website = normalize_website_url(website)
    
    try:
        # Start processing with progress tracking
        job_id = start_company_processing(company_name)
        
        # Create company data object
        company_data = CompanyData(
            name=company_name,
            website=website
        )
        
        # Process company using the main pipeline (same as research functionality)
        result = current_pipeline.process_single_company(company_name, website, job_id=job_id)
        
        # Check if processing was successful  
        if result and result.company_description:
            success = True  # process_single_company handles Pinecone storage internally
            
            # Mark job as completed (preserve existing results if concurrent scraper already set them)
            from src.progress_logger import complete_company_processing, progress_logger
            
            # Check if concurrent scraper already set detailed results
            existing_progress = progress_logger.get_progress(job_id)
            existing_results = existing_progress.get('results', {}) if existing_progress else {}
            
            # If concurrent scraper set results, preserve them; otherwise use minimal results
            if existing_results and existing_results.get('company'):
                # Concurrent scraper already set detailed results, don't override
                pass
            else:
                # Fallback results for non-concurrent path
                complete_company_processing(
                    job_id=job_id, 
                    success=True, 
                    summary=f"Successfully processed {company_name}",
                    results={
                        'company': result.dict(),
                        'company_id': result.id, 
                        'pages_processed': len(result.pages_crawled) if result.pages_crawled else 0,
                        'success': True
                    }
                )
            
            # Prepare token usage and cost data
            token_data = {
                'total_input_tokens': getattr(result, 'total_input_tokens', 0),
                'total_output_tokens': getattr(result, 'total_output_tokens', 0),
                'total_cost_usd': round(getattr(result, 'total_cost_usd', 0.0), 6),
                'llm_calls_count': len(getattr(result, 'llm_calls_breakdown', []))
            }
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'company_id': result.id,  # Include company ID for viewing details
                'company_name': result.name,
                'sales_intelligence': result.company_description,
                'pages_processed': len(result.pages_crawled) if result.pages_crawled else 0,
                'processing_time': result.crawl_duration,
                'stored_in_pinecone': success,
                'token_usage': token_data,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            # Mark job as failed
            from src.progress_logger import complete_company_processing
            error_msg = result.scrape_error if result else 'Processing failed - no result returned'
            complete_company_processing(
                job_id=job_id, 
                success=False, 
                error=error_msg
            )
            
            return jsonify({
                'success': False,
                'job_id': job_id,
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        # Mark job as failed due to exception
        from progress_logger import complete_company_processing
        complete_company_processing(
            job_id=job_id, 
            success=False, 
            error=f'Processing failed: {str(e)}'
        )
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/cancel-current-job', methods=['POST'])
def cancel_current_job():
    """Cancel the currently running processing job"""
    try:
        print(f"🛑 CANCEL: Cancel request received")
        
        # Get current job info
        current_job = progress_logger.get_current_job_progress()
        
        if current_job:
            job_id = current_job.get('job_id')
            company_name = current_job.get('company_name')
            print(f"🛑 CANCEL: Found current job {job_id} for {company_name}")
            
            # Mark the job as failed/cancelled
            progress_logger.complete_job(
                job_id=job_id,
                success=False,
                error="Cancelled by user",
                result_summary="Processing was cancelled by the user"
            )
            
            print(f"🛑 CANCEL: Job {job_id} marked as cancelled")
            
            return jsonify({
                'success': True,
                'message': f'Successfully cancelled processing for {company_name}',
                'cancelled_job': job_id
            })
        else:
            print(f"🛑 CANCEL: No current job found to cancel")
            return jsonify({
                'success': True,
                'message': 'No active job found to cancel'
            })
            
    except Exception as e:
        print(f"🛑 CANCEL: Error cancelling job: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to cancel job: {str(e)}'
        }), 500

@app.route('/api/search', methods=['GET'])
def search_companies():
    """API endpoint for searching existing companies"""
    try:
        query = request.args.get('q', '').strip().lower()
        
        if not query or len(query) < 2:
            return jsonify({'results': []})
        
        # Smart suggestions based on the query
        smart_suggestions = []
        
        # Get companies from actual database
        company_database = {}
        if pipeline and pipeline.pinecone_client:
            try:
                # Query Pinecone for all companies
                dummy_embedding = [0.0] * 1536
                results = pipeline.pinecone_client.index.query(
                    vector=dummy_embedding,
                    top_k=50,
                    include_metadata=True
                )
                
                for match in results.matches:
                    metadata = match.metadata or {}
                    company_name = metadata.get('company_name', '').lower()
                    if company_name:
                        # Clean up company name for key
                        key = company_name.replace(' ', '').replace('.', '').replace(',', '').lower()
                        company_database[key] = {
                            'name': metadata.get('company_name', ''),
                            'industry': metadata.get('industry', 'Unknown'),
                            'business_model': metadata.get('business_model', 'Unknown'),
                            'website': metadata.get('website', '')
                        }
            except Exception as e:
                print(f"Database query failed: {e}")
                # Return empty if database fails - no hardcoded fallback
                return jsonify({'results': []})
        
        # Find matches that start with the query (more restrictive)
        for key, company in company_database.items():
            if key.startswith(query):  # Only show if company name starts with query
                smart_suggestions.append({
                    'name': company['name'],
                    'website': company.get('website', f"https://{key}.com"),
                    'industry': company['industry'],
                    'business_model': company['business_model']
                })
                
        # If no exact start matches, then allow contains matches but mark them as secondary
        if not smart_suggestions:
            for key, company in company_database.items():
                if query in key and len(query) >= 3:  # Only for longer queries
                    smart_suggestions.append({
                        'name': company['name'],
                        'website': company.get('website', f"https://{key}.com"),
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
def get_job_progress(job_id):
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
        job_id = request.args.get('job_id')
        
        if job_id:
            # Get specific job progress
            progress_data = progress_logger.get_progress(job_id)
        else:
            # Get current job progress
            progress_data = progress_logger.get_current_job_progress()
            
            # If no current job, check for recently failed jobs
            if not progress_data:
                all_progress = progress_logger.get_progress()
                recent_failed_jobs = []
                
                # Look for jobs that failed in the last 30 seconds (much shorter window)
                import time
                current_time = time.time()
                
                for job_id_key, job_data in all_progress.get("jobs", {}).items():
                    if job_data.get("status") == "failed" and job_data.get("end_time"):
                        try:
                            end_time = datetime.fromisoformat(job_data["end_time"]).timestamp()
                            if current_time - end_time < 30:  # Only 30 seconds for failed jobs
                                recent_failed_jobs.append((job_id_key, job_data))
                        except:
                            pass
                
                if recent_failed_jobs:
                    # Return the most recent failed job
                    recent_failed_jobs.sort(key=lambda x: x[1].get("end_time", ""), reverse=True)
                    most_recent_failed = recent_failed_jobs[0][1]
                    
                    return jsonify({
                        "status": "recent_failure",
                        "progress": most_recent_failed,
                        "message": f"Recent job failed: {most_recent_failed.get('error', 'Unknown error')}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        if not progress_data:
            
            # Check for recently completed jobs in the last 30 seconds
            all_progress = progress_logger.get_progress()
            recent_completed_jobs = []
            
            import time
            current_time = time.time()
            
            for job_id_key, job_data in all_progress.get("jobs", {}).items():
                if job_data.get("status") in ["completed", "failed"] and job_data.get("end_time"):
                    try:
                        end_time = datetime.fromisoformat(job_data["end_time"]).timestamp()
                        if current_time - end_time < 30:  # Within last 30 seconds
                            recent_completed_jobs.append((job_id_key, job_data))
                    except Exception as e:
                        pass
            
            if recent_completed_jobs:
                # Return the most recent completed job
                recent_completed_jobs.sort(key=lambda x: x[1].get("end_time", ""), reverse=True)
                most_recent_completed = recent_completed_jobs[0][1]
                
                return jsonify({
                    "status": "recent_completion",
                    "progress": most_recent_completed,
                    "message": f"Recent job completed: {most_recent_completed.get('company_name')}",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return jsonify({
                "status": "no_active_job", 
                "message": "No active processing job found"
            })
        
        
        return jsonify({
            "status": "success",
            "progress": progress_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/progress/all', methods=['GET'])
def get_all_progress_data():
    """Get all progress data"""
    try:
        all_progress = progress_logger.get_progress()
        return jsonify({
            "status": "success",
            "data": all_progress,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error", 
            "error": str(e)
        }), 500

@app.route('/api/companies')
def list_companies():
    """List companies with search and pagination support"""
    if not pipeline:
        return jsonify({
            'success': False,
            'error': 'Theodore pipeline not initialized',
            'companies': [],
            'total': 0,
            'page': 1,
            'page_size': 25,
            'total_pages': 0
        }), 500
    
    try:
        # Get query parameters
        search_query = request.args.get('search', '').strip().lower()
        industry_filter = request.args.get('industry', '').strip()
        business_model_filter = request.args.get('business_model', '').strip()
        company_size_filter = request.args.get('company_size', '').strip()
        page = max(1, int(request.args.get('page', 1)))
        page_size = min(100, max(1, int(request.args.get('page_size', 25))))
        
        # Get all companies from Pinecone (increase limit for filtering)
        companies = []
        
        # Query Pinecone for all vectors (using a dummy query)
        dummy_embedding = [0.0] * 1536  # Standard embedding size
        results = pipeline.pinecone_client.index.query(
            vector=dummy_embedding,
            top_k=500,  # Increased for better search/filtering
            include_metadata=True
        )
        
        # Extract and normalize company data
        for match in results.matches:
            metadata = match.metadata or {}
            company = {
                'id': match.id,
                'name': metadata.get('company_name', 'Unknown'),
                'website': metadata.get('website', ''),
                'industry': metadata.get('industry', ''),
                'business_model': metadata.get('business_model', ''),
                'company_size': metadata.get('company_size', ''),
                'last_updated': metadata.get('last_updated', ''),
                'has_sales_intelligence': bool(metadata.get('has_description', False) or metadata.get('company_description', '')),
                # Classification data
                'saas_classification': metadata.get('saas_classification'),
                'classification_confidence': metadata.get('classification_confidence'),
                'classification_justification': metadata.get('classification_justification'),
                'is_saas': metadata.get('is_saas'),
                # Business Model Framework
                'business_model_framework': metadata.get('business_model_framework', ''),
                # Additional fields for better search
                'value_proposition': metadata.get('value_proposition', ''),
                'target_market': metadata.get('target_market', ''),
                'company_description': metadata.get('company_description', '')
            }
            companies.append(company)
        
        # Apply search filter
        if search_query:
            filtered_companies = []
            for company in companies:
                # Search in multiple fields
                searchable_text = ' '.join([
                    str(company.get('name', '') or ''),
                    str(company.get('industry', '') or ''),
                    str(company.get('business_model', '') or ''),
                    str(company.get('saas_classification', '') or ''),
                    str(company.get('business_model_framework', '') or ''),
                    str(company.get('value_proposition', '') or ''),
                    str(company.get('target_market', '') or ''),
                    str(company.get('company_description', '') or '')
                ]).lower()
                
                if search_query in searchable_text:
                    filtered_companies.append(company)
            companies = filtered_companies
        
        # Apply industry filter
        if industry_filter:
            companies = [c for c in companies if c.get('industry', '').lower() == industry_filter.lower()]
        
        # Apply business model filter
        if business_model_filter:
            companies = [c for c in companies if c.get('business_model', '').lower() == business_model_filter.lower()]
        
        # Apply company size filter
        if company_size_filter:
            companies = [c for c in companies if c.get('company_size', '').lower() == company_size_filter.lower()]
        
        # Sort companies by name
        companies.sort(key=lambda x: x.get('name', '').lower())
        
        # Calculate pagination
        total_companies = len(companies)
        total_pages = (total_companies + page_size - 1) // page_size
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_companies = companies[start_index:end_index]
        
        # Get unique industries for filter dropdown
        unique_industries = sorted(list(set(c.get('industry', '') for c in companies if c.get('industry', ''))))
        
        return jsonify({
            'success': True,
            'companies': paginated_companies,
            'total': total_companies,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'showing_start': start_index + 1 if total_companies > 0 else 0,
            'showing_end': min(end_index, total_companies),
            'filters': {
                'industries': unique_industries,
                'current_search': search_query,
                'current_industry': industry_filter,
                'current_business_model': business_model_filter,
                'current_company_size': company_size_filter
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to list companies: {str(e)}',
            'companies': [],
            'total': 0,
            'page': 1,
            'page_size': 25,
            'total_pages': 0
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
        
        # Helper function to parse JSON fields safely
        def parse_json_field(value):
            if isinstance(value, str) and value.strip():
                try:
                    import json
                    return json.loads(value)
                except:
                    return value
            return value if value else {}
        
        # Helper function to split comma-separated strings
        def split_field(value):
            if isinstance(value, str) and value.strip():
                return [item.strip() for item in value.split(',') if item.strip()]
            return value if isinstance(value, list) else []
        
        # Helper function to safely convert to int
        def safe_int_convert(value):
            if isinstance(value, int):
                return value
            elif isinstance(value, float):
                return int(value)
            elif isinstance(value, str):
                if value.lower() in ['unknown', 'none', '']:
                    return 0
                try:
                    return int(float(value))
                except (ValueError, TypeError):
                    return 0
            else:
                return 0
        
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
                'scrape_status': metadata.get('scrape_status', 'unknown'),
                
                # ENHANCED FIELDS - Now included in API response
                'raw_content_length': len(metadata.get('raw_content', '')),
                'founding_year': metadata.get('founding_year'),
                'location': metadata.get('location', ''),
                'employee_count_range': metadata.get('employee_count_range', ''),
                'value_proposition': metadata.get('value_proposition', ''),
                'funding_status': metadata.get('funding_status', ''),
                'company_culture': metadata.get('company_culture', ''),
                'company_stage': metadata.get('company_stage', ''),
                
                # List fields (split from comma-separated strings)
                'leadership_team': split_field(metadata.get('leadership_team', '')),
                'key_services': split_field(metadata.get('key_services', '')),
                'tech_stack': split_field(metadata.get('tech_stack', '')),
                'competitive_advantages': split_field(metadata.get('competitive_advantages', '')),
                'products_services_offered': split_field(metadata.get('products_services_offered', '')),
                'partnerships': split_field(metadata.get('partnerships', '')),
                'awards': split_field(metadata.get('awards', '')),
                'recent_news_events': split_field(metadata.get('recent_news_events', '')),
                'pain_points': split_field(metadata.get('pain_points', '')),
                
                # Structured fields (parse from JSON strings)
                'contact_info': parse_json_field(metadata.get('contact_info', '')),
                'social_media': parse_json_field(metadata.get('social_media', '')),
                
                # Job-related fields that frontend expects (with safe conversion)
                'has_job_listings': bool(safe_int_convert(metadata.get('job_listings_count', 0)) > 0),
                'job_listings_count': safe_int_convert(metadata.get('job_listings_count', 0)),
                'job_listings_details': split_field(metadata.get('job_listings_details', '')),
                'job_listings': metadata.get('job_listings', 'Job data unavailable'),
                
                # SaaS Classification fields
                'saas_classification': metadata.get('saas_classification'),
                'is_saas': metadata.get('is_saas'),
                'classification_confidence': metadata.get('classification_confidence'),
                'classification_justification': metadata.get('classification_justification'),
                'classification_timestamp': metadata.get('classification_timestamp'),
                
                # Scraping details (basic info from metadata)
                'scraped_urls_count': len(split_field(metadata.get('scraped_urls', ''))),
                'llm_interactions_count': metadata.get('llm_interactions_count', 0)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get company details: {str(e)}'}), 500

@app.route('/api/company/<company_id>/scraping-details')
def get_company_scraping_details(company_id):
    """Get detailed scraping information including URLs, LLM prompts, and vector content"""
    if not pipeline:
        return jsonify({'error': 'Theodore pipeline not initialized'}), 500
    
    try:
        # Fetch from Pinecone 
        result = pipeline.pinecone_client.index.fetch(ids=[company_id])
        
        if company_id not in result.vectors:
            return jsonify({'error': 'Company not found'}), 404
        
        vector_data = result.vectors[company_id]
        metadata = vector_data.metadata
        
        # Helper function to parse JSON fields safely  
        def parse_json_field(value):
            if isinstance(value, str) and value.strip():
                try:
                    import json
                    return json.loads(value)
                except:
                    return value
            return value if value else {}
        
        # Helper function to split comma-separated strings
        def split_field(value):
            if isinstance(value, str) and value.strip():
                return [item.strip() for item in value.split(',') if item.strip()]
            return value if isinstance(value, list) else []
        
        return jsonify({
            'success': True,
            'company_id': company_id,
            'company_name': metadata.get('company_name', 'Unknown'),
            'scraping_details': {
                'scraped_urls': split_field(metadata.get('scraped_urls', '')),
                'scraped_urls_count': metadata.get('scraped_urls_count', 0),
                'llm_interactions_count': metadata.get('llm_interactions_count', 0),
                'crawl_duration': metadata.get('crawl_duration', 0),
                'scrape_status': metadata.get('scrape_status', 'unknown'),
                'pages_crawled': metadata.get('pages_crawled', []),
                # Token usage and cost data
                'total_input_tokens': metadata.get('total_input_tokens', 0),
                'total_output_tokens': metadata.get('total_output_tokens', 0),
                'total_cost_usd': metadata.get('total_cost_usd', 0.0),
                'llm_calls_count': metadata.get('llm_calls_count', 0)
            },
            'note': 'Full vector content with LLM prompts and scraped content is stored in the vector embedding. Use the main company endpoint for basic details.'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get scraping details: {str(e)}'}), 500

@app.route('/api/company/<company_id>/update', methods=['PUT'])
def update_company(company_id):
    """Update an existing company record"""
    if not pipeline:
        return jsonify({'error': 'Theodore pipeline not initialized'}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No update data provided'}), 400
        
        # First, fetch the existing company data
        result = pipeline.pinecone_client.index.fetch(ids=[company_id])
        
        if company_id not in result.vectors:
            return jsonify({'error': 'Company not found'}), 404
        
        vector_data = result.vectors[company_id]
        existing_metadata = dict(vector_data.metadata)
        
        # Update metadata with new values
        updatable_fields = [
            'name', 'website', 'industry', 'business_model', 'company_size', 
            'founding_year', 'location', 'employee_count_range', 'company_description',
            'value_proposition', 'target_market', 'key_services', 'tech_stack',
            'funding_status', 'geographic_scope'
        ]
        
        updated_fields = []
        for field in updatable_fields:
            if field in data:
                # Handle special field mappings
                if field == 'name':
                    existing_metadata['company_name'] = data[field]
                    updated_fields.append('company_name')
                elif field == 'key_services' and isinstance(data[field], list):
                    existing_metadata['key_services'] = ', '.join(data[field])
                    updated_fields.append('key_services')
                elif field == 'tech_stack' and isinstance(data[field], list):
                    existing_metadata['tech_stack'] = ', '.join(data[field])
                    updated_fields.append('tech_stack')
                else:
                    existing_metadata[field] = data[field]
                    updated_fields.append(field)
        
        # Add update timestamp
        from datetime import datetime
        existing_metadata['last_updated'] = datetime.utcnow().isoformat()
        updated_fields.append('last_updated')
        
        # Update the vector in Pinecone (keeping the same embedding)
        pipeline.pinecone_client.index.upsert(
            vectors=[(company_id, vector_data.values, existing_metadata)]
        )
        
        return jsonify({
            'success': True,
            'message': f'Company updated successfully',
            'updated_fields': updated_fields,
            'company_id': company_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to update company: {str(e)}'}), 500

@app.route('/api/research/start', methods=['POST'])
def start_research():
    """Start research for a single company"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        website = data.get('website', '').strip()
        
        if not company_name or not website:
            return jsonify({'error': 'Company name and website are required'}), 400
        
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Initialize research manager if not exists
        if not hasattr(pipeline, 'research_manager'):
            from src.legacy.research_manager import ResearchManager
            pipeline.research_manager = ResearchManager(
                intelligent_scraper=pipeline.scraper,
                pinecone_client=pipeline.pinecone_client,
                bedrock_client=pipeline.bedrock_client
            )
        
        job_id = pipeline.research_manager.start_research(company_name, website)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'company_name': company_name,
            'message': f'Research started for {company_name}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to start research: {str(e)}'}), 500

@app.route('/api/research/bulk', methods=['POST'])
def start_bulk_research():
    """Start research for multiple companies"""
    try:
        data = request.get_json()
        companies = data.get('companies', [])
        
        if not companies:
            return jsonify({'error': 'No companies provided'}), 400
        
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Initialize research manager if not exists
        if not hasattr(pipeline, 'research_manager'):
            from src.legacy.research_manager import ResearchManager
            pipeline.research_manager = ResearchManager(
                intelligent_scraper=pipeline.scraper,
                pinecone_client=pipeline.pinecone_client,
                bedrock_client=pipeline.bedrock_client
            )
        
        job_ids = pipeline.research_manager.start_bulk_research(companies)
        
        return jsonify({
            'success': True,
            'job_ids': job_ids,
            'total_started': len(job_ids),
            'message': f'Research started for {len(job_ids)} companies'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to start bulk research: {str(e)}'}), 500

@app.route('/api/research/progress/<job_id>', methods=['GET'])
def get_research_progress(job_id):
    """Get progress for a specific research job"""
    try:
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Initialize research manager if not exists  
        if not hasattr(pipeline, 'research_manager'):
            from src.legacy.research_manager import ResearchManager
            pipeline.research_manager = ResearchManager(
                intelligent_scraper=pipeline.scraper,
                pinecone_client=pipeline.pinecone_client,
                bedrock_client=pipeline.bedrock_client
            )
        
        progress = pipeline.research_manager.get_research_progress(job_id)
        
        if not progress:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'success': True,
            'progress': progress
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get progress: {str(e)}'}), 500

@app.route('/api/research/progress', methods=['GET'])
def get_all_research_progress():
    """Get progress for all research jobs"""
    try:
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Initialize research manager if not exists  
        if not hasattr(pipeline, 'research_manager'):
            from src.legacy.research_manager import ResearchManager
            pipeline.research_manager = ResearchManager(
                intelligent_scraper=pipeline.scraper,
                pinecone_client=pipeline.pinecone_client,
                bedrock_client=pipeline.bedrock_client
            )
        
        all_progress = pipeline.research_manager.get_all_research_progress()
        summary = pipeline.research_manager.get_research_summary()
        
        return jsonify({
            'success': True,
            'progress': all_progress,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get progress: {str(e)}'}), 500

@app.route('/api/research/cleanup', methods=['POST'])
def cleanup_research_jobs():
    """Clean up completed research jobs"""
    try:
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours', 24)
        
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Initialize research manager if not exists  
        if not hasattr(pipeline, 'research_manager'):
            from src.legacy.research_manager import ResearchManager
            pipeline.research_manager = ResearchManager(
                intelligent_scraper=pipeline.scraper,
                pinecone_client=pipeline.pinecone_client,
                bedrock_client=pipeline.bedrock_client
            )
        
        pipeline.research_manager.cleanup_completed_jobs(max_age_hours)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up completed jobs older than {max_age_hours} hours'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to cleanup: {str(e)}'}), 500

@app.route('/api/research/prompts/available', methods=['GET'])
def get_available_research_prompts():
    """Get all available research prompts with metadata"""
    try:
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Initialize research manager if not exists
        if not hasattr(pipeline, 'research_manager'):
            from src.legacy.research_manager import ResearchManager
            pipeline.research_manager = ResearchManager(
                intelligent_scraper=pipeline.scraper,
                pinecone_client=pipeline.pinecone_client,
                bedrock_client=pipeline.bedrock_client
            )
        
        prompts_summary = pipeline.research_manager.get_available_prompts()
        
        return jsonify({
            'success': True,
            'prompts': prompts_summary,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get prompts: {str(e)}'}), 500

@app.route('/api/research/prompts/estimate', methods=['POST'])
def estimate_research_cost():
    """Estimate cost for selected research prompts"""
    try:
        data = request.get_json()
        selected_prompts = data.get('selected_prompts', [])
        
        if not selected_prompts:
            return jsonify({'error': 'No prompts selected'}), 400
        
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Initialize research manager if not exists
        if not hasattr(pipeline, 'research_manager'):
            from src.legacy.research_manager import ResearchManager
            pipeline.research_manager = ResearchManager(
                intelligent_scraper=pipeline.scraper,
                pinecone_client=pipeline.pinecone_client,
                bedrock_client=pipeline.bedrock_client
            )
        
        cost_estimate = pipeline.research_manager.estimate_research_cost(selected_prompts)
        
        return jsonify({
            'success': True,
            'cost_estimate': cost_estimate,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to estimate cost: {str(e)}'}), 500

@app.route('/api/research/structured/start', methods=['POST'])
def start_structured_research():
    """Start structured research with selected prompts"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        website = data.get('website', '').strip()
        selected_prompts = data.get('selected_prompts', [])
        include_base_research = data.get('include_base_research', True)
        
        if not company_name or not website:
            return jsonify({'error': 'Company name and website are required'}), 400
        
        if not selected_prompts:
            return jsonify({'error': 'At least one research prompt must be selected'}), 400
        
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Initialize research manager if not exists
        if not hasattr(pipeline, 'research_manager'):
            from src.legacy.research_manager import ResearchManager
            pipeline.research_manager = ResearchManager(
                intelligent_scraper=pipeline.scraper,
                pinecone_client=pipeline.pinecone_client,
                bedrock_client=pipeline.bedrock_client
            )
        
        # Get cost estimate
        cost_estimate = pipeline.research_manager.estimate_research_cost(selected_prompts)
        
        # Start structured research
        session_id = pipeline.research_manager.research_company_with_prompts(
            company_name=company_name,
            website=website,
            selected_prompts=selected_prompts,
            include_base_research=include_base_research
        )
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'company_name': company_name,
            'selected_prompts': selected_prompts,
            'cost_estimate': cost_estimate,
            'message': f'Structured research started for {company_name} with {len(selected_prompts)} prompts'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to start structured research: {str(e)}'}), 500

@app.route('/api/research/structured/session/<session_id>', methods=['GET'])
def get_structured_research_session(session_id):
    """Get structured research session details"""
    try:
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Initialize research manager if not exists
        if not hasattr(pipeline, 'research_manager'):
            from src.legacy.research_manager import ResearchManager
            pipeline.research_manager = ResearchManager(
                intelligent_scraper=pipeline.scraper,
                pinecone_client=pipeline.pinecone_client,
                bedrock_client=pipeline.bedrock_client
            )
        
        session = pipeline.research_manager.get_research_session(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Convert session to dictionary for JSON response
        session_data = {
            'session_id': session.session_id,
            'company_name': session.company_name,
            'website': session.website,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'selected_prompts': session.selected_prompts,
            'total_cost': session.total_cost,
            'total_tokens': session.total_tokens,
            'success_rate': session.success_rate,
            'results': [
                {
                    'prompt_id': result.prompt_id,
                    'prompt_name': result.prompt_name,
                    'success': result.success,
                    'result_data': result.result_data,
                    'error_message': result.error_message,
                    'cost': result.cost,
                    'execution_time': result.execution_time
                }
                for result in (session.results or [])
            ],
            'raw_company_data': session.raw_company_data
        }
        
        return jsonify({
            'success': True,
            'session': session_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get session: {str(e)}'}), 500

@app.route('/api/research/structured/sessions', methods=['GET'])
def get_recent_structured_sessions():
    """Get recent structured research sessions"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Initialize research manager if not exists
        if not hasattr(pipeline, 'research_manager'):
            from src.legacy.research_manager import ResearchManager
            pipeline.research_manager = ResearchManager(
                intelligent_scraper=pipeline.scraper,
                pinecone_client=pipeline.pinecone_client,
                bedrock_client=pipeline.bedrock_client
            )
        
        sessions = pipeline.research_manager.get_recent_sessions(limit)
        
        # Convert sessions to dictionaries
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'session_id': session.session_id,
                'company_name': session.company_name,
                'website': session.website,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'total_prompts': len(session.selected_prompts or []),
                'total_cost': session.total_cost,
                'success_rate': session.success_rate,
                'status': 'completed' if session.end_time else 'running'
            })
        
        return jsonify({
            'success': True,
            'sessions': sessions_data,
            'total': len(sessions_data)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get sessions: {str(e)}'}), 500

@app.route('/api/research/structured/export/<session_id>', methods=['GET'])
def export_structured_research_results(session_id):
    """Export structured research results"""
    try:
        format_type = request.args.get('format', 'json').lower()
        
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Initialize research manager if not exists
        if not hasattr(pipeline, 'research_manager'):
            from src.legacy.research_manager import ResearchManager
            pipeline.research_manager = ResearchManager(
                intelligent_scraper=pipeline.scraper,
                pinecone_client=pipeline.pinecone_client,
                bedrock_client=pipeline.bedrock_client
            )
        
        exported_data = pipeline.research_manager.export_session_results(session_id, format_type)
        
        return jsonify({
            'success': True,
            'format': format_type,
            'data': exported_data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to export results: {str(e)}'}), 500

@app.route('/api/classify-unknown-industries', methods=['POST'])
def classify_unknown_industries():
    """Re-classify companies with unknown/missing industries using existing research data"""
    try:
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not available'}), 500
        
        # Get all companies from Pinecone
        dummy_embedding = [0.0] * 1536
        results = pipeline.pinecone_client.index.query(
            vector=dummy_embedding,
            top_k=100,
            include_metadata=True
        )
        
        companies_to_classify = []
        for match in results.matches:
            metadata = match.metadata or {}
            industry = metadata.get('industry', '').lower()
            
            # Find companies with unknown/missing industry that have research data
            if (not industry or industry == 'unknown' or industry == '') and metadata.get('company_description'):
                companies_to_classify.append({
                    'id': match.id,
                    'name': metadata.get('company_name', 'Unknown'),
                    'description': metadata.get('company_description', ''),
                    'business_model': metadata.get('business_model', ''),
                    'key_services': metadata.get('key_services', ''),
                    'target_market': metadata.get('target_market', ''),
                    'value_proposition': metadata.get('value_proposition', '')
                })
        
        if not companies_to_classify:
            return jsonify({
                'success': True,
                'message': 'No companies with unknown industries found that have research data',
                'classified': 0
            })
        
        # Import the prompt
        from src.legacy.similarity_prompts import INDUSTRY_CLASSIFICATION_FROM_RESEARCH_PROMPT
        
        classified_count = 0
        results_log = []
        
        for company in companies_to_classify:
            try:
                # Create prompt with ALL available company data
                prompt = INDUSTRY_CLASSIFICATION_FROM_RESEARCH_PROMPT.format(
                    company_name=company['name'],
                    website=company.get('website', 'Not available'),
                    company_description=company['description'],
                    value_proposition=company.get('value_proposition', 'Not available'),
                    business_model=company['business_model'],
                    target_market=company['target_market'],
                    key_services=company['key_services'],
                    competitive_advantages=company.get('competitive_advantages', 'Not available'),
                    pain_points=company.get('pain_points', 'Not available'),
                    location=company.get('location', 'Not available'),
                    founding_year=company.get('founding_year', 'Not available'),
                    company_size=company.get('company_size', 'Not available'),
                    employee_count_range=company.get('employee_count_range', 'Not available'),
                    funding_status=company.get('funding_status', 'Not available'),
                    tech_stack=company.get('tech_stack', 'Not available'),
                    has_chat_widget=company.get('has_chat_widget', 'Not available'),
                    has_forms=company.get('has_forms', 'Not available'),
                    certifications=company.get('certifications', 'Not available'),
                    partnerships=company.get('partnerships', 'Not available'),
                    awards=company.get('awards', 'Not available'),
                    leadership_team=company.get('leadership_team', 'Not available'),
                    recent_news=company.get('recent_news', 'Not available')
                )
                
                # Get industry classification from LLM
                response = pipeline.bedrock_client.analyze_content(prompt)
                
                # Extract industry from response
                industry = None
                if 'Industry:' in response:
                    industry_text = response.split('Industry:')[1].strip().split('\n')[0].strip()
                    if industry_text and industry_text.lower() not in ['unknown', 'insufficient data']:
                        industry = industry_text
                elif response.strip() and response.strip().lower() not in ['unknown', 'insufficient data']:
                    industry = response.strip()
                
                # Update the company in Pinecone
                if industry:
                    # Fetch current vector data
                    current_data = pipeline.pinecone_client.index.fetch(ids=[company['id']])
                    if company['id'] in current_data.vectors:
                        current_metadata = current_data.vectors[company['id']].metadata
                        current_values = current_data.vectors[company['id']].values
                        
                        # Update metadata with new industry
                        current_metadata['industry'] = industry
                        
                        # Upsert back to Pinecone
                        pipeline.pinecone_client.index.upsert([(
                            company['id'],
                            current_values,
                            current_metadata
                        )])
                        
                        classified_count += 1
                        results_log.append(f"✅ {company['name']}: {industry}")
                    else:
                        results_log.append(f"❌ {company['name']}: Could not fetch current data")
                else:
                    results_log.append(f"⚠️ {company['name']}: LLM could not determine industry")
                    
            except Exception as e:
                results_log.append(f"❌ {company['name']}: Error - {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully classified {classified_count} companies',
            'classified': classified_count,
            'total_candidates': len(companies_to_classify),
            'results': results_log
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to classify industries: {str(e)}'}), 500


# =============================================================================
# CLASSIFICATION API ENDPOINTS (Phase 3)
# =============================================================================

@app.route('/api/classification/stats', methods=['GET'])
def get_classification_stats():
    """Get overall classification statistics"""
    try:
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not initialized'}), 500
        
        # Query all vectors to get classification stats
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,  # Get more results for stats
            include_metadata=True,
            include_values=False
        )
        
        stats = {
            'total_companies': len(query_result.matches),
            'classified_companies': 0,
            'saas_companies': 0,
            'non_saas_companies': 0,
            'categories': {},
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        for match in query_result.matches:
            metadata = match.metadata or {}
            
            # Check if company is classified
            is_classified = metadata.get('saas_classification') is not None
            if is_classified:
                stats['classified_companies'] += 1
                
                # Count SaaS vs Non-SaaS
                if metadata.get('is_saas'):
                    stats['saas_companies'] += 1
                else:
                    stats['non_saas_companies'] += 1
                
                # Count categories
                category = metadata.get('saas_classification', 'Unknown')
                stats['categories'][category] = stats['categories'].get(category, 0) + 1
                
                # Confidence distribution
                confidence = metadata.get('classification_confidence', 0)
                if confidence >= 0.8:
                    stats['confidence_distribution']['high'] += 1
                elif confidence >= 0.6:
                    stats['confidence_distribution']['medium'] += 1
                else:
                    stats['confidence_distribution']['low'] += 1
        
        # Calculate percentages
        total = stats['total_companies']
        if total > 0:
            stats['classification_percentage'] = round((stats['classified_companies'] / total) * 100, 1)
            stats['saas_percentage'] = round((stats['saas_companies'] / total) * 100, 1)
        else:
            stats['classification_percentage'] = 0
            stats['saas_percentage'] = 0
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get classification stats: {str(e)}'}), 500

@app.route('/api/classification/export', methods=['GET'])
def export_classification_data():
    """Export classification data in CSV format"""
    try:
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not initialized'}), 500
        
        # Get export format from query params
        export_format = request.args.get('format', 'json').lower()
        include_unclassified = request.args.get('include_unclassified', 'false').lower() == 'true'
        
        # Query all vectors
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        export_data = []
        for match in query_result.matches:
            metadata = match.metadata or {}
            
            # Skip unclassified if not requested
            is_classified = metadata.get('saas_classification') is not None
            if not include_unclassified and not is_classified:
                continue
            
            company_data = {
                'company_name': metadata.get('company_name', 'Unknown'),
                'website': metadata.get('website', ''),
                'industry': metadata.get('industry', ''),
                'is_saas': metadata.get('is_saas'),
                'saas_classification': metadata.get('saas_classification'),
                'classification_confidence': metadata.get('classification_confidence'),
                'classification_justification': metadata.get('classification_justification'),
                'database_id': match.id,
                'classification_timestamp': metadata.get('classification_timestamp')
            }
            export_data.append(company_data)
        
        if export_format == 'csv':
            import csv
            from io import StringIO
            
            output = StringIO()
            if export_data:
                writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
            
            from flask import Response
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=theodore_classification_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                }
            )
        else:
            # JSON export
            return jsonify({
                'export_timestamp': datetime.now().isoformat(),
                'total_companies': len(export_data),
                'format': 'json',
                'data': export_data
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to export classification data: {str(e)}'}), 500

@app.route('/api/classification/company/<company_id>', methods=['GET'])
def get_company_classification(company_id):
    """Get detailed classification information for a specific company"""
    try:
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not initialized'}), 500
        
        # Fetch company from Pinecone
        fetch_result = pipeline.pinecone_client.index.fetch(ids=[company_id])
        
        if not fetch_result.vectors or company_id not in fetch_result.vectors:
            return jsonify({'error': 'Company not found'}), 404
        
        vector_data = fetch_result.vectors[company_id]
        metadata = vector_data.metadata or {}
        
        classification_data = {
            'company_id': company_id,
            'company_name': metadata.get('company_name', 'Unknown'),
            'website': metadata.get('website', ''),
            'industry': metadata.get('industry', ''),
            'is_saas': metadata.get('is_saas'),
            'saas_classification': metadata.get('saas_classification'),
            'classification_confidence': metadata.get('classification_confidence'),
            'classification_justification': metadata.get('classification_justification'),
            'classification_timestamp': metadata.get('classification_timestamp'),
            'is_classified': metadata.get('saas_classification') is not None
        }
        
        return jsonify(classification_data)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get company classification: {str(e)}'}), 500

@app.route('/api/classification/categories', methods=['GET'])
def get_classification_categories():
    """Get all available classification categories with counts"""
    try:
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not initialized'}), 500
        
        # Import classification taxonomy
        try:
            from src.classification.classification_prompts import SAAS_BUSINESS_MODEL_TAXONOMY
            taxonomy_categories = list(SAAS_BUSINESS_MODEL_TAXONOMY.keys())
        except ImportError:
            # Fallback categories if taxonomy not available
            taxonomy_categories = [
                "AdTech", "AI/ML Platform", "Analytics Platform", "API Management",
                "Business Intelligence", "CRM", "Customer Support", "DevOps Platform",
                "E-commerce Platform", "HR Tech", "IT Consulting Services", "Marketing Automation",
                "Project Management", "Security Platform", "Social Media Management"
            ]
        
        # Query database to get actual usage counts
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        category_counts = {}
        total_classified = 0
        
        for match in query_result.matches:
            metadata = match.metadata or {}
            category = metadata.get('saas_classification')
            
            if category:
                total_classified += 1
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Build response with taxonomy and actual counts
        categories = []
        for category in taxonomy_categories:
            categories.append({
                'name': category,
                'count': category_counts.get(category, 0),
                'in_taxonomy': True
            })
        
        # Add any categories found in database but not in taxonomy
        for category, count in category_counts.items():
            if category not in taxonomy_categories:
                categories.append({
                    'name': category,
                    'count': count,
                    'in_taxonomy': False
                })
        
        # Sort by count (descending)
        categories.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify({
            'categories': categories,
            'total_categories': len(categories),
            'total_classified_companies': total_classified,
            'taxonomy_categories': len(taxonomy_categories)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get classification categories: {str(e)}'}), 500

@app.route('/api/classification/batch', methods=['POST'])
def batch_classify_companies():
    """Classify multiple unclassified companies in batch"""
    try:
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not initialized'}), 500
        
        data = request.get_json()
        batch_size = min(int(data.get('batch_size', 10)), 50)  # Max 50 companies
        force_reclassify = data.get('force_reclassify', False)
        
        # Query all companies to find unclassified ones
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        # Filter for unclassified companies (or all if force_reclassify)
        candidates = []
        for match in query_result.matches:
            metadata = match.metadata or {}
            is_classified = metadata.get('saas_classification') is not None
            
            if force_reclassify or not is_classified:
                company_name = metadata.get('company_name')
                website = metadata.get('website', '')
                industry = metadata.get('industry', '')
                
                if company_name:  # Only include companies with names
                    candidates.append({
                        'id': match.id,
                        'name': company_name,
                        'website': website,
                        'industry': industry,
                        'metadata': metadata
                    })
        
        if not candidates:
            return jsonify({
                'success': False,
                'message': 'No unclassified companies found',
                'processed': 0,
                'total_candidates': 0
            })
        
        # Limit to batch size
        companies_to_process = candidates[:batch_size]
        
        # Import classification system
        try:
            from src.classification.classification_system import SaaSBusinessModelClassifier
            classifier = SaaSBusinessModelClassifier()
        except ImportError:
            return jsonify({'error': 'Classification system not available'}), 500
        
        results = []
        successful_classifications = 0
        
        for i, company in enumerate(companies_to_process):
            try:
                print(f"🏷️ Classifying {i+1}/{len(companies_to_process)}: {company['name']}")
                
                # Prepare company data for classification
                company_data = {
                    'name': company['name'],
                    'website': company['website'],
                    'industry': company['industry'],
                    'description': company['metadata'].get('value_proposition', ''),
                    'products_services': company['metadata'].get('products_services_offered', '')
                }
                
                # Perform classification
                classification_result = classifier.classify_company(company_data)
                
                if classification_result and classification_result.get('success'):
                    # Update company metadata with classification
                    updated_metadata = company['metadata'].copy()
                    updated_metadata.update({
                        'is_saas': classification_result['is_saas'],
                        'saas_classification': classification_result['category'],
                        'classification_confidence': classification_result['confidence'],
                        'classification_justification': classification_result['justification'],
                        'classification_timestamp': datetime.now().isoformat()
                    })
                    
                    # Update in Pinecone
                    update_result = pipeline.pinecone_client.index.update(
                        id=company['id'],
                        metadata=updated_metadata
                    )
                    
                    successful_classifications += 1
                    results.append({
                        'company_name': company['name'],
                        'status': 'success',
                        'category': classification_result['category'],
                        'is_saas': classification_result['is_saas'],
                        'confidence': classification_result['confidence']
                    })
                    
                    print(f"✅ Successfully classified {company['name']} as {classification_result['category']}")
                    
                else:
                    results.append({
                        'company_name': company['name'],
                        'status': 'failed',
                        'error': 'Classification failed'
                    })
                    print(f"❌ Failed to classify {company['name']}")
                    
            except Exception as company_error:
                results.append({
                    'company_name': company['name'],
                    'status': 'failed',
                    'error': str(company_error)
                })
                print(f"❌ Error classifying {company['name']}: {company_error}")
        
        return jsonify({
            'success': True,
            'message': f'Batch classification completed: {successful_classifications}/{len(companies_to_process)} successful',
            'processed': len(companies_to_process),
            'successful': successful_classifications,
            'total_candidates': len(candidates),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': f'Batch classification failed: {str(e)}'}), 500

@app.route('/api/batch/validate', methods=['POST'])
def validate_google_sheet():
    """Validate Google Sheet access and structure"""
    try:
        data = request.get_json()
        sheet_id = data.get('sheet_id')
        
        if not sheet_id:
            return jsonify({'error': 'Sheet ID is required'}), 400
        
        # Check if service account is configured
        from pathlib import Path
        service_account_file = Path('config/credentials/theodore-service-account.json')
        
        if not service_account_file.exists():
            return jsonify({
                'error': 'Google Sheets service account not configured',
                'details': 'Please add theodore-service-account.json to config/credentials/ folder'
            }), 400
        
        # Import and initialize Google Sheets client
        try:
            from src.sheets_integration.google_sheets_service_client import GoogleSheetsServiceClient
            sheets_client = GoogleSheetsServiceClient(service_account_file)
        except ImportError as e:
            return jsonify({
                'error': 'Google Sheets integration not available',
                'details': str(e)
            }), 500
        
        # Validate sheet access
        is_accessible = sheets_client.validate_sheet_access(sheet_id)
        
        if not is_accessible:
            return jsonify({
                'error': 'Cannot access Google Sheet',
                'details': 'Make sure the sheet is shared with the service account email'
            }), 403
        
        # Get sheet info
        try:
            spreadsheet = sheets_client.service.spreadsheets().get(
                spreadsheetId=sheet_id
            ).execute()
            
            sheet_title = spreadsheet['properties']['title']
            sheets = spreadsheet.get('sheets', [])
            sheet_names = [sheet['properties']['title'] for sheet in sheets]
            
            # Try to get company count from the Companies sheet
            companies_count = 0
            try:
                # Read data from the Companies sheet (assuming it's the first sheet or named "Companies")
                companies_sheet_name = None
                for sheet in sheets:
                    name = sheet['properties']['title']
                    if 'companies' in name.lower() or sheet == sheets[0]:  # Use Companies sheet or first sheet
                        companies_sheet_name = name
                        break
                
                if companies_sheet_name:
                    # Get the data range (assuming headers in row 1, data starts from row 2)
                    range_name = f"{companies_sheet_name}!A:A"  # Read entire column A to count all rows
                    result = sheets_client.service.spreadsheets().values().get(
                        spreadsheetId=sheet_id,
                        range=range_name
                    ).execute()
                    
                    values = result.get('values', [])
                    # Count non-empty rows, skipping header (first row)
                    if len(values) > 1:  # Make sure there's more than just the header
                        data_rows = values[1:]  # Skip header row
                        companies_count = len([row for row in data_rows if row and len(row) > 0 and row[0].strip()])
                    else:
                        companies_count = 0
                    
            except Exception as count_error:
                logger.warning(f"Could not get company count: {count_error}")
                companies_count = 0
            
            return jsonify({
                'success': True,
                'sheet_id': sheet_id,
                'title': sheet_title,
                'sheets': sheet_names,
                'companies_count': companies_count,
                'message': f'Successfully validated access to "{sheet_title}"'
            })
            
        except Exception as e:
            return jsonify({
                'error': 'Failed to get sheet information',
                'details': str(e)
            }), 500
        
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@app.route('/api/batch/process', methods=['POST'])
def start_batch_processing():
    """Start batch processing of companies from Google Sheet"""
    try:
        data = request.get_json()
        sheet_id = data.get('sheet_id')
        batch_size = data.get('batch_size', 10)
        start_row = data.get('start_row', 2)
        max_concurrent = data.get('max_concurrent', 3)  # Max concurrent companies
        
        if not sheet_id:
            return jsonify({'error': 'Sheet ID is required'}), 400
        
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not initialized'}), 500
        
        # Validate parameters
        if batch_size < 1 or batch_size > 1000:
            return jsonify({'error': 'Batch size must be between 1 and 1000'}), 400
        
        if start_row < 2:
            return jsonify({'error': 'Start row must be at least 2 (first data row)'}), 400
            
        if max_concurrent < 1 or max_concurrent > 10:
            return jsonify({'error': 'Max concurrent must be between 1 and 10'}), 400
        
        # Check if service account is configured
        from pathlib import Path
        service_account_file = Path('config/credentials/theodore-service-account.json')
        
        if not service_account_file.exists():
            return jsonify({
                'error': 'Google Sheets service account not configured',
                'details': 'Please add theodore-service-account.json to config/credentials/ folder'
            }), 400
        
        # Import and initialize Google Sheets client
        try:
            from src.sheets_integration.google_sheets_service_client import GoogleSheetsServiceClient
            sheets_client = GoogleSheetsServiceClient(service_account_file)
        except ImportError as e:
            return jsonify({
                'error': 'Google Sheets integration not available',
                'details': str(e)
            }), 500
        
        # Validate sheet access
        is_accessible = sheets_client.validate_sheet_access(sheet_id)
        if not is_accessible:
            return jsonify({
                'error': 'Cannot access Google Sheet',
                'details': 'Make sure the sheet is shared with the service account email'
            }), 403
        
        # Read company data from sheet
        try:
            # Find the Companies sheet
            spreadsheet = sheets_client.service.spreadsheets().get(
                spreadsheetId=sheet_id
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            companies_sheet_name = None
            for sheet in sheets:
                name = sheet['properties']['title']
                if 'companies' in name.lower() or sheet == sheets[0]:
                    companies_sheet_name = name
                    break
            
            if not companies_sheet_name:
                return jsonify({'error': 'Could not find Companies sheet'}), 400
            
            # Calculate end row
            end_row = start_row + batch_size - 1
            
            # Read the data range (assuming Company Name in column A, Website in column B)
            range_name = f"{companies_sheet_name}!A{start_row}:B{end_row}"
            result = sheets_client.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return jsonify({'error': f'No data found in rows {start_row}-{end_row}'}), 400
            
            # Extract company data
            companies_to_process = []
            for i, row in enumerate(values):
                if len(row) >= 1 and row[0].strip():  # Has company name
                    company_name = row[0].strip()
                    website = row[1].strip() if len(row) > 1 and row[1].strip() else None
                    
                    companies_to_process.append({
                        'name': company_name,
                        'website': website,
                        'row_number': start_row + i
                    })
            
            if not companies_to_process:
                return jsonify({'error': 'No valid companies found in the specified range'}), 400
            
            # Enforce batch size limit - only process exactly the requested number
            if len(companies_to_process) > batch_size:
                logger.warning(f"Found {len(companies_to_process)} companies, limiting to requested {batch_size}")
                companies_to_process = companies_to_process[:batch_size]
            
            # Generate job ID for tracking
            import uuid
            import time
            job_id = f"batch_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
            
            # Start processing companies in background
            import threading
            def process_batch():
                process_companies_batch(job_id, companies_to_process, sheet_id, companies_sheet_name, max_concurrent)
            
            thread = threading.Thread(target=process_batch)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'companies_count': len(companies_to_process),
                'start_row': start_row,
                'end_row': end_row,
                'max_concurrent': max_concurrent,
                'message': f'Started batch processing {len(companies_to_process)} companies with {max_concurrent} concurrent workers'
            })
            
        except Exception as e:
            return jsonify({
                'error': 'Failed to read sheet data',
                'details': str(e)
            }), 500
        
    except Exception as e:
        return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500

def process_companies_batch(job_id, companies, sheet_id, sheet_name, max_concurrent=3):
    """Process a batch of companies using antoine pipeline with detailed tracking"""
    from src.progress_logger import progress_logger
    from pathlib import Path
    from src.sheets_integration.google_sheets_service_client import GoogleSheetsServiceClient
    from antoine.batch.batch_processor import AntoineBatchProcessor
    from src.models import CompanyIntelligenceConfig
    import sys
    sys.path.append('config')
    from sheets_column_mapping import company_data_to_sheet_row, calculate_llm_cost
    
    # Initialize progress and sheets
    progress_logger.start_batch_job(job_id, len(companies))
    service_account_file = Path('config/credentials/theodore-service-account.json')
    sheets_client = GoogleSheetsServiceClient(service_account_file)
    
    # Initialize antoine batch processor with parallel processing
    config = CompanyIntelligenceConfig()
    bedrock_client = pipeline.bedrock_client if pipeline else None
    
    # Create progress callback for batch updates
    def batch_progress_callback(processed_count, message, current_company):
        progress_logger.update_batch_progress(job_id, processed_count, message, current_company)
    
    batch_processor = AntoineBatchProcessor(
        config=config,
        bedrock_client=bedrock_client,
        max_concurrent_companies=max_concurrent,  # Use configurable parallel processing
        enable_resource_pooling=True,
        progress_callback=batch_progress_callback
    )
    
    # Convert companies for batch processor
    companies_data = []
    company_map = {}  # Map name to full company info including row
    
    for company in companies:
        companies_data.append({
            'name': company['name'],
            'website': company.get('website', '')
        })
        company_map[company['name']] = company
    
    # Process batch with antoine
    progress_logger.update_batch_progress(job_id, 0, 
        f"Starting parallel processing with Antoine pipeline ({max_concurrent} concurrent workers)...")
    
    try:
        batch_result = batch_processor.process_batch(
            companies=companies_data,
            batch_name=f"Sheet batch {job_id}"
        )
        
        # Process results and update sheets
        successful_companies = []
        failed_companies = []
        
        for i, company_result in enumerate(batch_result.company_results):
            original_company = company_map.get(company_result.name)
            if not original_company:
                continue
                
            row_number = original_company['row_number']
            
            if company_result.scrape_status == "success":
                # Get costs - either from LLM calls breakdown or from the already calculated totals
                llm_calls = getattr(company_result, 'llm_calls_breakdown', [])
                
                if llm_calls:
                    # Calculate from breakdown
                    total_cost = 0.0
                    total_input_tokens = 0
                    total_output_tokens = 0
                    
                    for call in llm_calls:
                        if 'cost_usd' in call:
                            total_cost += call.get('cost_usd', 0.0)
                        else:
                            # Fallback calculation
                            model = call.get('model', 'unknown')
                            input_tokens = call.get('input_tokens', 0)
                            output_tokens = call.get('output_tokens', 0)
                            cost = calculate_llm_cost(model, input_tokens, output_tokens)
                            total_cost += cost
                        
                        total_input_tokens += call.get('input_tokens', 0)
                        total_output_tokens += call.get('output_tokens', 0)
                    
                    # Update company data with calculated costs
                    company_result.total_cost_usd = total_cost
                    company_result.total_input_tokens = total_input_tokens
                    company_result.total_output_tokens = total_output_tokens
                else:
                    # Use the costs already set by antoine_scraper_adapter
                    total_cost = getattr(company_result, 'total_cost_usd', 0.0)
                    total_input_tokens = getattr(company_result, 'total_input_tokens', 0)
                    total_output_tokens = getattr(company_result, 'total_output_tokens', 0)
                
                # Convert to sheet row format
                row_data = company_data_to_sheet_row(company_result)
                
                # Update sheet with all fields
                try:
                    updates = []
                    for column_letter, value in row_data.items():
                        if value:  # Only update non-empty values
                            updates.append({
                                'range': f'Details!{column_letter}{row_number}',
                                'values': [[value]]
                            })
                    
                    if updates:
                        sheets_client.service.spreadsheets().values().batchUpdate(
                            spreadsheetId=sheet_id,
                            body={'valueInputOption': 'RAW', 'data': updates}
                        ).execute()
                    
                    # Also update Companies sheet status
                    sheets_client.update_company_status(
                        spreadsheet_id=sheet_id,
                        row_number=row_number,
                        status='completed',
                        progress='100%'
                    )
                    
                    # Save to Pinecone for searchability
                    pinecone_saved = False
                    try:
                        if company_result.company_description:
                            # Generate embedding
                            embedding = pipeline.bedrock_client.get_embeddings(company_result.company_description)
                            company_result.embedding = embedding
                            
                            # Save to Pinecone
                            pinecone_saved = pipeline.pinecone_client.upsert_company(company_result)
                            
                            if pinecone_saved:
                                logger.info(f"✅ Saved {company_result.name} to Pinecone")
                            else:
                                logger.warning(f"⚠️ Failed to save {company_result.name} to Pinecone")
                        else:
                            logger.warning(f"⚠️ No description for {company_result.name}, skipping Pinecone")
                    except Exception as pinecone_error:
                        logger.error(f"❌ Pinecone error for {company_result.name}: {pinecone_error}")
                        pinecone_saved = False
                    
                    # Update progress message after all operations
                    if pinecone_saved:
                        progress_logger.update_batch_progress(job_id, i + 1, 
                            f"✅ Completed {company_result.name} - saved to Sheets & Pinecone (row {row_number})")
                    else:
                        progress_logger.update_batch_progress(job_id, i + 1, 
                            f"✅ Completed {company_result.name} - saved to Sheets only (row {row_number})")
                    
                    successful_companies.append({
                        'name': company_result.name,
                        'row': row_number,
                        'status': 'success',
                        'cost_usd': total_cost,
                        'tokens': {
                            'input': total_input_tokens,
                            'output': total_output_tokens
                        },
                        'pinecone_saved': pinecone_saved
                    })
                    
                    logger.info(f"Added {company_result.name} to successful_companies: cost=${total_cost}, tokens={total_input_tokens}+{total_output_tokens}")
                    
                except Exception as sheet_error:
                    progress_logger.update_batch_progress(job_id, i + 1, 
                        f"⚠️ Processed {company_result.name} but failed to save: {str(sheet_error)}")
                
            else:
                # Handle failures - write minimal data
                try:
                    error_msg = company_result.scrape_error or 'Processing failed'
                    updates = [
                        {'range': f'Details!AC{row_number}', 'values': [['failed']]},  # Status
                        {'range': f'Details!AD{row_number}', 'values': [[error_msg]]},  # Error
                        {'range': f'Details!AB{row_number}', 'values': [[company_result.name]]},  # Name
                        {'range': f'Details!AE{row_number}', 'values': [[original_company.get('website', '')]]}  # Website
                    ]
                    
                    sheets_client.service.spreadsheets().values().batchUpdate(
                        spreadsheetId=sheet_id,
                        body={'valueInputOption': 'RAW', 'data': updates}
                    ).execute()
                    
                    # Update Companies sheet status
                    sheets_client.update_company_status(
                        spreadsheet_id=sheet_id,
                        row_number=row_number,
                        status='failed',
                        error_message=error_msg
                    )
                    
                except:
                    pass  # Continue even if sheet write fails
                
                failed_companies.append({
                    'name': company_result.name,
                    'row': row_number,
                    'error': company_result.scrape_error or 'Unknown error'
                })
                
                progress_logger.update_batch_progress(job_id, i + 1, 
                    f"❌ Failed {company_result.name}: {company_result.scrape_error}")
        
        # Calculate totals
        total_cost = sum(c.get('cost_usd', 0) for c in successful_companies)
        total_input_tokens = sum(c.get('tokens', {}).get('input', 0) for c in successful_companies)
        total_output_tokens = sum(c.get('tokens', {}).get('output', 0) for c in successful_companies)
        
        logger.info(f"Batch processing complete: {len(successful_companies)} successful, {len(failed_companies)} failed")
        logger.info(f"Total cost: ${total_cost:.2f}, Total tokens: {total_input_tokens} + {total_output_tokens}")
        logger.info(f"Batch result stats: {batch_result.successful} successful, {batch_result.failed} failed from Antoine processor")
        
        # Complete batch processing
        progress_logger.complete_batch_job(
            job_id, 
            len(successful_companies), 
            len(failed_companies),
            {
                'successful': successful_companies, 
                'failed': failed_companies,
                'total_cost_usd': total_cost,
                'total_input_tokens': total_input_tokens,
                'total_output_tokens': total_output_tokens,
                'total_duration': batch_result.total_duration,
                'companies_per_minute': batch_result.companies_per_minute,
                'parallel_efficiency': batch_result.resource_stats.get('parallel_efficiency', 0)
            }
        )
        
        # Cleanup
        batch_processor.shutdown()
        
    except Exception as e:
        # Handle batch processing error
        logger.error(f"Batch processing error: {e}")
        progress_logger.update_batch_progress(job_id, len(companies), 
            f"❌ Batch processing failed: {str(e)}")
        progress_logger.complete_batch_job(job_id, 0, len(companies), {'error': str(e)})

@app.route('/api/batch/progress/<job_id>', methods=['GET'])
def get_batch_progress(job_id):
    """Get progress of batch processing job"""
    try:
        from src.progress_logger import progress_logger
        progress = progress_logger.get_batch_progress(job_id)
        
        if not progress:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify(progress)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get progress: {str(e)}'}), 500

@app.route('/api/batch/stream/<job_id>')
def stream_batch_progress(job_id):
    """Stream real-time batch progress updates using Server-Sent Events"""
    from flask import Response
    from src.progress_logger import progress_logger
    import json
    import time
    
    def generate():
        """Generate SSE events for batch progress"""
        last_update = None
        no_update_count = 0
        max_no_updates = 60  # Stop after 60 seconds of no updates
        
        while True:
            try:
                # Get current progress
                progress = progress_logger.get_batch_progress(job_id)
                
                if not progress:
                    yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                    break
                
                # Check if progress has changed
                current_status = progress.get('status')
                current_processed = progress.get('processed', 0)
                current_message = progress.get('current_message', '')
                
                current_update = f"{current_status}-{current_processed}-{current_message}"
                
                if current_update != last_update:
                    # Progress changed, send update
                    yield f"data: {json.dumps(progress)}\n\n"
                    last_update = current_update
                    no_update_count = 0
                else:
                    no_update_count += 1
                
                # Check if job is completed
                if current_status == 'completed':
                    # Send final update and close
                    yield f"data: {json.dumps({'event': 'complete', 'progress': progress})}\n\n"
                    break
                
                # Check for timeout
                if no_update_count >= max_no_updates:
                    yield f"data: {json.dumps({'event': 'timeout', 'message': 'No updates for 60 seconds'})}\n\n"
                    break
                
                # Sleep before next check
                time.sleep(1)
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Disable nginx buffering
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/classification/unclassified', methods=['GET'])
def get_unclassified_companies():
    """Get list of companies that haven't been classified yet"""
    try:
        if not pipeline:
            return jsonify({'error': 'Theodore pipeline not initialized'}), 500
        
        # Query all companies
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        unclassified = []
        for match in query_result.matches:
            metadata = match.metadata or {}
            is_classified = metadata.get('saas_classification') is not None
            
            if not is_classified:
                company_name = metadata.get('company_name')
                if company_name:  # Only include companies with names
                    unclassified.append({
                        'id': match.id,
                        'company_name': company_name,
                        'website': metadata.get('website', ''),
                        'industry': metadata.get('industry', ''),
                        'has_description': bool(metadata.get('value_proposition')),
                        'has_products': bool(metadata.get('products_services_offered'))
                    })
        
        return jsonify({
            'unclassified_companies': unclassified,
            'total_unclassified': len(unclassified),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get unclassified companies: {str(e)}'}), 500

# User Prompt Management API Endpoints (Authenticated)
@app.route('/api/prompts/library')
@api_auth_optional
def get_user_prompt_library():
    """Get user's complete prompt library"""
    try:
        from src.user_prompt_service import UserPromptService
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Initialize prompt service
        prompt_service = UserPromptService(pinecone_client=pipeline.pinecone_client if pipeline else None)
        
        # Get user's library
        library = prompt_service.get_user_prompt_library(current_user.id)
        
        return jsonify({
            'success': True,
            'library': {
                'user_id': library.user_id,
                'total_prompts': library.total_prompts,
                'total_usage': library.total_usage,
                'avg_library_success_rate': library.avg_library_success_rate,
                'prompts': [
                    {
                        'id': p.id,
                        'prompt_type': p.prompt_type,
                        'prompt_name': p.prompt_name,
                        'prompt_content': p.prompt_content,
                        'description': p.description,
                        'is_active': p.is_active,
                        'is_default': p.is_default,
                        'usage_count': p.usage_count,
                        'last_used': p.last_used.isoformat() if p.last_used else None,
                        'avg_success_rate': p.avg_success_rate,
                        'avg_processing_time': p.avg_processing_time,
                        'avg_cost_per_use': p.avg_cost_per_use,
                        'created_at': p.created_at.isoformat(),
                        'updated_at': p.updated_at.isoformat()
                    } for p in library.prompts
                ]
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting user prompt library: {e}")
        return jsonify({'error': f'Failed to get prompt library: {str(e)}'}), 500


@app.route('/api/prompts', methods=['POST'])
@api_auth_optional
def create_user_prompt():
    """Create a new user prompt"""
    try:
        from src.user_prompt_service import UserPromptService
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['prompt_type', 'prompt_name', 'prompt_content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Initialize prompt service
        prompt_service = UserPromptService(pinecone_client=pipeline.pinecone_client if pipeline else None)
        
        # Create new prompt
        new_prompt = prompt_service.create_prompt(
            user_id=current_user.id,
            prompt_type=data['prompt_type'],
            prompt_name=data['prompt_name'],
            prompt_content=data['prompt_content'],
            description=data.get('description'),
            is_default=data.get('is_default', False)
        )
        
        if new_prompt:
            return jsonify({
                'success': True,
                'prompt': {
                    'id': new_prompt.id,
                    'prompt_type': new_prompt.prompt_type,
                    'prompt_name': new_prompt.prompt_name,
                    'prompt_content': new_prompt.prompt_content,
                    'description': new_prompt.description,
                    'is_default': new_prompt.is_default,
                    'created_at': new_prompt.created_at.isoformat()
                },
                'message': 'Prompt created successfully'
            })
        else:
            return jsonify({'error': 'Failed to create prompt'}), 500
        
    except Exception as e:
        logger.error(f"Error creating user prompt: {e}")
        return jsonify({'error': f'Failed to create prompt: {str(e)}'}), 500


@app.route('/api/prompts/<prompt_id>', methods=['PUT'])
@api_auth_optional
def update_user_prompt(prompt_id):
    """Update an existing user prompt"""
    try:
        from src.user_prompt_service import UserPromptService
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Initialize prompt service
        prompt_service = UserPromptService(pinecone_client=pipeline.pinecone_client if pipeline else None)
        
        # Update prompt
        updated_prompt = prompt_service.update_prompt(
            user_id=current_user.id,
            prompt_id=prompt_id,
            **data
        )
        
        if updated_prompt:
            return jsonify({
                'success': True,
                'prompt': {
                    'id': updated_prompt.id,
                    'prompt_type': updated_prompt.prompt_type,
                    'prompt_name': updated_prompt.prompt_name,
                    'prompt_content': updated_prompt.prompt_content,
                    'description': updated_prompt.description,
                    'is_default': updated_prompt.is_default,
                    'updated_at': updated_prompt.updated_at.isoformat()
                },
                'message': 'Prompt updated successfully'
            })
        else:
            return jsonify({'error': 'Prompt not found or update failed'}), 404
        
    except Exception as e:
        logger.error(f"Error updating user prompt: {e}")
        return jsonify({'error': f'Failed to update prompt: {str(e)}'}), 500


@app.route('/api/prompts/<prompt_id>', methods=['DELETE'])
@api_auth_optional
def delete_user_prompt(prompt_id):
    """Delete a user prompt"""
    try:
        from src.user_prompt_service import UserPromptService
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Initialize prompt service
        prompt_service = UserPromptService(pinecone_client=pipeline.pinecone_client if pipeline else None)
        
        # Delete prompt
        success = prompt_service.delete_prompt(current_user.id, prompt_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Prompt deleted successfully'
            })
        else:
            return jsonify({'error': 'Prompt not found or deletion failed'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting user prompt: {e}")
        return jsonify({'error': f'Failed to delete prompt: {str(e)}'}), 500


@app.route('/api/prompts/<prompt_id>/set-default', methods=['POST'])
@api_auth_optional
def set_default_prompt(prompt_id):
    """Set a prompt as default for its type"""
    try:
        from src.user_prompt_service import UserPromptService
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Initialize prompt service
        prompt_service = UserPromptService(pinecone_client=pipeline.pinecone_client if pipeline else None)
        
        # Set as default
        success = prompt_service.set_default_prompt(current_user.id, prompt_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Default prompt updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to set default prompt'}), 500
        
    except Exception as e:
        logger.error(f"Error setting default prompt: {e}")
        return jsonify({'error': f'Failed to set default prompt: {str(e)}'}), 500


@app.route('/api/prompts/type/<prompt_type>')
@api_auth_optional
def get_prompts_by_type(prompt_type):
    """Get all user prompts of a specific type"""
    try:
        from src.user_prompt_service import UserPromptService
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Initialize prompt service
        prompt_service = UserPromptService(pinecone_client=pipeline.pinecone_client if pipeline else None)
        
        # Get prompts by type
        prompts = prompt_service.get_prompts_by_type(current_user.id, prompt_type)
        
        return jsonify({
            'success': True,
            'prompt_type': prompt_type,
            'prompts': [
                {
                    'id': p.id,
                    'prompt_name': p.prompt_name,
                    'prompt_content': p.prompt_content,
                    'description': p.description,
                    'is_default': p.is_default,
                    'usage_count': p.usage_count,
                    'avg_success_rate': p.avg_success_rate,
                    'created_at': p.created_at.isoformat()
                } for p in prompts
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting prompts by type: {e}")
        return jsonify({'error': f'Failed to get prompts: {str(e)}'}), 500


@app.route('/api/prompts/export')
@api_auth_optional
def export_user_prompts():
    """Export user's prompts for backup/sharing"""
    try:
        from src.user_prompt_service import UserPromptService
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Initialize prompt service
        prompt_service = UserPromptService(pinecone_client=pipeline.pinecone_client if pipeline else None)
        
        # Export prompts
        export_data = prompt_service.export_user_prompts(current_user.id)
        
        return jsonify({
            'success': True,
            'export_data': export_data
        })
        
    except Exception as e:
        logger.error(f"Error exporting user prompts: {e}")
        return jsonify({'error': f'Failed to export prompts: {str(e)}'}), 500


@app.route('/api/prompts/import', methods=['POST'])
@api_auth_optional
def import_user_prompts():
    """Import prompts from export data"""
    try:
        from src.user_prompt_service import UserPromptService
        from flask_login import current_user
        
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data or 'import_data' not in data:
            return jsonify({'error': 'No import data provided'}), 400
        
        # Initialize prompt service
        prompt_service = UserPromptService(pinecone_client=pipeline.pinecone_client if pipeline else None)
        
        # Import prompts
        success = prompt_service.import_user_prompts(current_user.id, data['import_data'])
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Prompts imported successfully'
            })
        else:
            return jsonify({'error': 'Failed to import prompts'}), 500
        
    except Exception as e:
        logger.error(f"Error importing user prompts: {e}")
        return jsonify({'error': f'Failed to import prompts: {str(e)}'}), 500


# Field Metrics API Endpoints
@app.route('/api/field-metrics/summary')
def get_field_metrics_summary():
    """Get field extraction performance summary"""
    try:
        # Check if pipeline is initialized
        if not pipeline:
            # Return mock data for demo purposes
            return jsonify({
                'success': True,
                'summary': {
                    'overall_performance': {
                        'average_success_rate': 0.75,
                        'total_fields_tracked': 53,
                        'best_performing_field': 'company_name',
                        'worst_performing_field': 'founding_year'
                    },
                    'field_breakdown': {
                        'company_description': {'success_rate': 0.85, 'total_attempts': 100},
                        'founding_year': {'success_rate': 0.25, 'total_attempts': 100},
                        'location': {'success_rate': 0.60, 'total_attempts': 100},
                        'employee_count_range': {'success_rate': 0.40, 'total_attempts': 100}
                    },
                    'recommendations': [
                        'Improve founding year extraction with specialized patterns',
                        'Location data often in footer - enhance footer parsing',
                        'Employee count typically on careers pages - prioritize these'
                    ]
                },
                'timestamp': datetime.now().isoformat(),
                'note': 'Using demo data - pipeline not initialized'
            })
        
        from src.field_metrics_service import FieldMetricsService
        
        # Initialize metrics service
        metrics_service = FieldMetricsService(pinecone_client=pipeline.pinecone_client)
        
        # Get overall performance summary
        summary = metrics_service.get_field_performance_summary()
        
        return jsonify({
            'success': True,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except ImportError:
        # Service not available, return demo data
        return jsonify({
            'success': True,
            'summary': {
                'overall_performance': {
                    'average_success_rate': 0.75,
                    'total_fields_tracked': 53,
                    'best_performing_field': 'company_name',
                    'worst_performing_field': 'founding_year'
                },
                'field_breakdown': {},
                'recommendations': []
            },
            'timestamp': datetime.now().isoformat(),
            'note': 'Field metrics service not available'
        })
    except Exception as e:
        logger.error(f"Error getting field metrics summary: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get field metrics: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/field-metrics/field/<field_name>')
def get_field_metrics(field_name):
    """Get detailed metrics for a specific field"""
    try:
        from src.field_metrics_service import FieldMetricsService
        
        # Initialize metrics service
        metrics_service = FieldMetricsService(pinecone_client=pipeline.pinecone_client if pipeline else None)
        
        # Get field-specific performance
        field_summary = metrics_service.get_field_performance_summary(field_name)
        
        return jsonify({
            'success': True,
            'field_name': field_name,
            'metrics': field_summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting metrics for field {field_name}: {e}")
        return jsonify({'error': f'Failed to get metrics for {field_name}: {str(e)}'}), 500


@app.route('/api/field-metrics/company/<company_id>/analysis')
def analyze_company_field_extraction(company_id):
    """Analyze field extraction success for a specific company"""
    try:
        from src.field_metrics_service import FieldMetricsService
        
        # Get company data
        if not pipeline or not pipeline.pinecone_client:
            return jsonify({'error': 'Pipeline not initialized'}), 500
        
        company = pipeline.pinecone_client.get_full_company_data(company_id)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Initialize metrics service and analyze
        metrics_service = FieldMetricsService(pinecone_client=pipeline.pinecone_client)
        analysis = metrics_service.analyze_company_extraction(company)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error analyzing company {company_id} field extraction: {e}")
        return jsonify({'error': f'Failed to analyze company field extraction: {str(e)}'}), 500


@app.route('/api/field-metrics/export')
def export_field_metrics():
    """Export comprehensive field metrics report"""
    try:
        # Check if pipeline is initialized
        if not pipeline:
            # Return demo report
            return jsonify({
                'success': True,
                'report': {
                    'export_date': datetime.now().isoformat(),
                    'total_companies_analyzed': 10,
                    'total_fields_tracked': 53,
                    'summary': {
                        'overall_performance': {
                            'average_success_rate': 0.75,
                            'total_fields_tracked': 53,
                            'best_performing_field': 'company_name',
                            'worst_performing_field': 'founding_year'
                        },
                        'field_breakdown': {
                            'company_description': {'success_rate': 0.85, 'total_attempts': 10},
                            'founding_year': {'success_rate': 0.25, 'total_attempts': 10},
                            'location': {'success_rate': 0.60, 'total_attempts': 10},
                            'employee_count_range': {'success_rate': 0.40, 'total_attempts': 10},
                            'tech_stack': {'success_rate': 0.70, 'total_attempts': 10},
                            'social_media': {'success_rate': 0.55, 'total_attempts': 10}
                        }
                    },
                    'note': 'Demo report - pipeline not initialized'
                },
                'timestamp': datetime.now().isoformat()
            })
        
        from src.field_metrics_service import FieldMetricsService
        
        # Initialize metrics service
        metrics_service = FieldMetricsService(pinecone_client=pipeline.pinecone_client)
        
        # Get export format from query params
        format_type = request.args.get('format', 'json')
        detailed = request.args.get('detailed', 'false').lower() == 'true'
        
        # Generate report
        report = metrics_service.export_metrics_report(format=format_type)
        
        return jsonify({
            'success': True,
            'report': report,
            'timestamp': datetime.now().isoformat()
        })
        
    except ImportError:
        # Service not available
        return jsonify({
            'success': True,
            'report': {
                'export_date': datetime.now().isoformat(),
                'error': 'Field metrics service not available',
                'summary': {}
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error exporting field metrics: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to export field metrics: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/ping')
def ping():
    """Simple ping endpoint for health checks"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'message': 'Theodore API is running'
    })

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(app.static_folder, 'favicon.ico')

if __name__ == '__main__':
    print("🚀 Starting Theodore Web UI...")
    print("🌐 Access at: http://localhost:5002")
    print("🔧 Google Search domain discovery enabled")
    app.run(debug=True, host='0.0.0.0', port=5002)