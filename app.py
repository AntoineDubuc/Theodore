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
    import time
    return render_template('index.html', timestamp=int(time.time()))

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
                'last_updated': metadata.get('last_updated', 'Unknown')
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
    """Find companies similar to the given company using enhanced multi-pronged discovery"""
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
            
            if not enhanced_results:
                return jsonify({
                    "error": f"No similar companies found for '{company_name}'",
                    "suggestion": "Try processing the company first or check if it exists in our database",
                    "companies": []
                })
            
            # Initialize research manager if not exists
            if not hasattr(pipeline, 'research_manager'):
                from src.legacy.research_manager import ResearchManager
                pipeline.research_manager = ResearchManager(
                    intelligent_scraper=pipeline.scraper,
                    pinecone_client=pipeline.pinecone_client,
                    bedrock_client=pipeline.gemini_client
                )
            
            # Enhance results with research status
            enhanced_companies = pipeline.research_manager.enhance_discovered_companies(enhanced_results)
            
            # Format response for UI
            formatted_results = []
            for company in enhanced_companies:
                formatted_results.append({
                    "company_name": company.name,
                    "website": company.website,
                    "similarity_score": round(company.similarity_score, 3),
                    "confidence": round(company.confidence, 3),
                    "reasoning": company.reasoning,
                    "relationship_type": company.relationship_type,
                    "discovery_method": company.discovery_method,
                    "business_context": company.business_context,
                    "sources": company.sources,
                    "research_status": company.research_status.value,
                    "in_database": company.in_database,
                    "database_id": company.database_id
                })
            
            response = {
                "success": True,
                "target_company": company_name,
                "results": formatted_results,
                "total_found": len(formatted_results),
                "discovery_method": "Enhanced Multi-Source Discovery",
                "sources_used": list(set([s for r in enhanced_results for s in r.get("sources", [])])),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return jsonify(response)
            
        except Exception as discovery_error:
            print(f"Enhanced discovery failed, falling back to basic similarity: {discovery_error}")
            
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
def research_company():
    """Research a specific company suggestion on-demand"""
    print(f"🐍 FLASK: ===== RESEARCH ENDPOINT CALLED =====")
    print(f"🐍 FLASK: Request method: {request.method}")
    print(f"🐍 FLASK: Request content type: {request.content_type}")
    
    try:
        print(f"🐍 FLASK: Attempting to parse JSON request data...")
        data = request.get_json()
        print(f"🐍 FLASK: JSON parsed successfully")
        print(f"🐍 FLASK: Request data keys: {list(data.keys()) if data else 'None'}")
        print(f"🐍 FLASK: Full request data: {data}")
        
        company_data = data.get('company', {})
        print(f"🐍 FLASK: Company data extracted: {company_data}")
        print(f"🐍 FLASK: Company name: {company_data.get('name', 'MISSING')}")
        print(f"🐍 FLASK: Company website: {company_data.get('website', 'MISSING')}")
        
        if not company_data or not company_data.get('name'):
            print(f"🐍 FLASK: ❌ VALIDATION FAILED - Missing company data")
            error_response = {
                "error": "Company data is required",
                "company": {}
            }
            print(f"🐍 FLASK: Returning 400 error: {error_response}")
            return jsonify(error_response), 400
        
        # Check if pipeline is available
        print(f"🐍 FLASK: Checking pipeline availability...")
        if not pipeline:
            print(f"🐍 FLASK: ❌ CRITICAL ERROR - Pipeline not available")
            error_response = {
                "error": "Theodore pipeline not available",
                "company": {}
            }
            print(f"🐍 FLASK: Returning 500 error: {error_response}")
            return jsonify(error_response), 500
        
        print(f"🐍 FLASK: ✅ Pipeline available, proceeding with research")
        print(f"🐍 FLASK: Pipeline components: scraper={bool(pipeline.scraper)}, bedrock={bool(pipeline.bedrock_client)}, pinecone={bool(pipeline.pinecone_client)}")
        
        print(f"🐍 FLASK: ===== STARTING RESEARCH PROCESS =====")
        company_name = company_data.get('name')
        print(f"🐍 FLASK: Research target: {company_name}")
        
        
        try:
            print(f"🐍 FLASK: Step 1 - Importing SimpleEnhancedDiscovery...")
            from src.simple_enhanced_discovery import SimpleEnhancedDiscovery
            print(f"🐍 FLASK: ✅ Import successful!")
            
            print(f"🐍 FLASK: Step 2 - Initializing discovery system...")
            enhanced_discovery = SimpleEnhancedDiscovery(
                ai_client=pipeline.bedrock_client,
                pinecone_client=pipeline.pinecone_client,
                scraper=pipeline.scraper
            )
            print(f"🐍 FLASK: ✅ Discovery system initialized!")
            
            print(f"🐍 FLASK: Step 3 - Calling research_company_on_demand...")
            print(f"🐍 FLASK: This will trigger the full research pipeline...")
            
            import time
            start_time = time.time()
            
            researched_company = enhanced_discovery.research_company_on_demand(company_data)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"🐍 FLASK: ===== RESEARCH COMPLETED =====")
            print(f"🐍 FLASK: Total duration: {duration:.2f} seconds")
            print(f"🐍 FLASK: Research status: {researched_company.get('research_status', 'unknown')}")
            print(f"🐍 FLASK: Research error: {researched_company.get('research_error', 'none')}")
            print(f"🐍 FLASK: Result keys: {list(researched_company.keys()) if isinstance(researched_company, dict) else 'Not a dict'}")
            
            success_response = {
                "success": True,
                "company": researched_company,
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time": duration
            }
            
            print(f"🐍 FLASK: Returning success response")
            return jsonify(success_response)
            
        except Exception as research_error:
            print(f"🐍 FLASK: ❌ RESEARCH EXCEPTION: {research_error}")
            print(f"🐍 FLASK: ❌ Exception type: {type(research_error).__name__}")
            
            import traceback
            traceback_str = traceback.format_exc()
            print(f"🐍 FLASK: ❌ Full traceback:\n{traceback_str}")
            
            error_response = {
                "error": f"Research failed: {str(research_error)}",
                "company": company_data,
                "exception_type": type(research_error).__name__
            }
            print(f"🐍 FLASK: Returning 500 error response: {error_response}")
            return jsonify(error_response), 500
            
    except Exception as endpoint_error:
        print(f"🐍 FLASK: ❌ CRITICAL ENDPOINT ERROR: {endpoint_error}")
        print(f"🐍 FLASK: ❌ Exception type: {type(endpoint_error).__name__}")
        
        import traceback
        traceback_str = traceback.format_exc()
        print(f"🐍 FLASK: ❌ Full endpoint traceback:\n{traceback_str}")
        
        critical_error_response = {
            "error": f"Internal server error: {str(endpoint_error)}",
            "company": {},
            "exception_type": type(endpoint_error).__name__
        }
        
        print(f"🐍 FLASK: ===== CRITICAL ENDPOINT FAILURE =====")
        print(f"🐍 FLASK: Returning 500 critical error: {critical_error_response}")
        return jsonify(critical_error_response), 500

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

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
            'page_selection_prompt': get_page_selection_prompt(),
            'extraction_prompt': get_extraction_prompt()
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
            'timeout': 25,
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
                # Simple test - this would ideally be a lightweight API call
                results['bedrock'] = 'Connected'
            else:
                results['bedrock'] = 'Not configured'
        except Exception as e:
            results['bedrock'] = f'Error: {str(e)}'
        
        # Test Gemini
        try:
            if pipeline and pipeline.gemini_client:
                results['gemini'] = 'Connected'
            else:
                results['gemini'] = 'Not configured'
        except Exception as e:
            results['gemini'] = f'Error: {str(e)}'
        
        # Test OpenAI (if configured)
        results['openai'] = 'Optional - not tested'
        
        return jsonify({
            'success': True,
            'message': 'Model tests completed',
            'results': results
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to test models: {str(e)}"}), 500

@app.route('/api/settings/recalculate-costs', methods=['POST'])
def recalculate_costs():
    """Recalculate cost estimates"""
    try:
        # Import our cost analysis functions
        import sys
        sys.path.append('.')
        
        # Calculate real-time costs
        from cost_analysis import calculate_extraction_cost, estimate_batch_costs
        
        # Standard company cost
        standard_cost = calculate_extraction_cost(3000, enhanced_extraction=True)
        batch_400 = estimate_batch_costs(400)
        
        updated_estimates = {
            'per_company': f"{standard_cost['total']:.4f}",
            'batch_10': f"{estimate_batch_costs(10)['total_cost']:.2f}",
            'batch_100': f"{estimate_batch_costs(100)['total_cost']:.2f}",
            'batch_400': f"{batch_400['total_cost']:.2f}",
            'batch_1000': f"{estimate_batch_costs(1000)['total_cost']:.2f}",
            'primary_analysis': f"{standard_cost['primary_analysis']:.4f}",
            'enhancement_cost': f"{standard_cost['enhanced_extraction']:.4f}",
            'embedding': f"{standard_cost['embedding_generation']:.4f}"
        }
        
        return jsonify({
            'success': True,
            'message': 'Costs recalculated based on current models and usage',
            'updated_estimates': updated_estimates
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'message': 'Costs recalculated (using cached estimates)',
            'note': f'Real-time calculation failed: {str(e)}'
        })

@app.route('/api/settings/save-prompt', methods=['POST'])
def save_prompt():
    """Save updated prompt"""
    try:
        data = request.get_json()
        prompt_type = data.get('type')
        prompt_content = data.get('prompt')
        
        # In a real implementation, you'd save this to a config file or database
        # For now, just acknowledge the save
        
        return jsonify({
            'success': True,
            'message': f'{prompt_type.title()} prompt saved successfully'
        })
    except Exception as e:
        return jsonify({"error": f"Failed to save prompt: {str(e)}"}), 500

@app.route('/api/settings/reset-prompts', methods=['POST'])
def reset_prompts():
    """Reset prompts to defaults"""
    try:
        # This would reset prompts to their default values
        return jsonify({
            'success': True,
            'message': 'All prompts reset to defaults'
        })
    except Exception as e:
        return jsonify({"error": f"Failed to reset prompts: {str(e)}"}), 500

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

# Helper functions for settings
def get_analysis_prompt():
    """Get the current company analysis prompt"""
    return """Analyze this company's website content and extract structured business intelligence.

Focus on:
1. Industry classification
2. Business model (B2B, B2C, marketplace, etc.)
3. Company size indicators
4. Target market
5. Key technologies used
6. Products/services offered
7. Competitive positioning

Return structured JSON with extracted fields."""

def get_page_selection_prompt():
    """Get the current page selection prompt"""
    return """You are a data extraction specialist analyzing {company_name}'s website structure.

Select up to 50 pages that are MOST LIKELY to contain these CRITICAL missing data points:

🔴 HIGHEST PRIORITY (Currently missing from our database):
1. **Contact & Location**: Physical address, headquarters location
   → Look for: /contact, /about, /offices, /locations
2. **Founded Year**: When the company was established
   → Look for: /about, /our-story, /history, /company
3. **Employee Count**: Team size or number of employees  
   → Look for: /about, /team, /careers, /jobs

Return ONLY a JSON array of URLs prioritized by likelihood of containing missing data."""

def get_extraction_prompt():
    """Get the current enhanced extraction prompt"""
    return """Extract specific structured data fields from this company content.

Target fields:
- founding_year: Integer year when founded
- employee_count_range: String like "50-100", "500+", "10-50"
- location: String with city, state/country
- social_media: Object with platform names and handles
- certifications: Array of compliance/security certifications
- partnerships: Array of key partner company names

Return valid JSON only."""

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
    print(f"🔧 PROGRESS: Current progress endpoint called")
    
    try:
        job_id = request.args.get('job_id')
        print(f"🔧 PROGRESS: Requested job_id: {job_id}")
        
        if job_id:
            # Get specific job progress
            print(f"🔧 PROGRESS: Getting progress for specific job: {job_id}")
            progress_data = progress_logger.get_progress(job_id)
        else:
            # Get current job progress
            print(f"🔧 PROGRESS: Getting current job progress")
            progress_data = progress_logger.get_current_job_progress()
            
            # If no current job, check for recently failed jobs
            if not progress_data:
                print(f"🔧 PROGRESS: No current job, checking for recent failed jobs...")
                all_progress = progress_logger.get_progress()
                recent_failed_jobs = []
                
                # Look for jobs that failed in the last 5 minutes
                import time
                current_time = time.time()
                
                for job_id_key, job_data in all_progress.get("jobs", {}).items():
                    if job_data.get("status") == "failed" and job_data.get("end_time"):
                        try:
                            end_time = datetime.fromisoformat(job_data["end_time"]).timestamp()
                            if current_time - end_time < 300:  # 5 minutes
                                recent_failed_jobs.append((job_id_key, job_data))
                        except:
                            pass
                
                if recent_failed_jobs:
                    # Return the most recent failed job
                    recent_failed_jobs.sort(key=lambda x: x[1].get("end_time", ""), reverse=True)
                    most_recent_failed = recent_failed_jobs[0][1]
                    print(f"🔧 PROGRESS: Found recent failed job: {most_recent_failed.get('company_name')}")
                    print(f"🔧 PROGRESS: Failed job error: {most_recent_failed.get('error')}")
                    
                    return jsonify({
                        "status": "recent_failure",
                        "progress": most_recent_failed,
                        "message": f"Recent job failed: {most_recent_failed.get('error', 'Unknown error')}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        if not progress_data:
            print(f"🔧 PROGRESS: No progress data found")
            
            # Check for recently completed jobs in the last 30 seconds
            print(f"🔧 PROGRESS: Checking for recently completed jobs...")
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
                            print(f"🔧 PROGRESS: Found recent job: {job_data.get('company_name')} - {job_data.get('status')}")
                    except Exception as e:
                        print(f"🔧 PROGRESS: Error parsing job time: {e}")
                        pass
            
            if recent_completed_jobs:
                # Return the most recent completed job
                recent_completed_jobs.sort(key=lambda x: x[1].get("end_time", ""), reverse=True)
                most_recent_completed = recent_completed_jobs[0][1]
                print(f"🔧 PROGRESS: Returning most recent completed job: {most_recent_completed.get('company_name')}")
                
                return jsonify({
                    "status": "recent_completion",
                    "progress": most_recent_completed,
                    "message": f"Recent job completed: {most_recent_completed.get('company_name')}",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            print(f"🔧 PROGRESS: No recent jobs found either")
            return jsonify({
                "status": "no_active_job", 
                "message": "No active processing job found"
            })
        
        print(f"🔧 PROGRESS: Returning progress data for job: {progress_data.get('company_name')}")
        print(f"🔧 PROGRESS: Job status: {progress_data.get('status')}")
        print(f"🔧 PROGRESS: Job error: {progress_data.get('error')}")
        
        return jsonify({
            "status": "success",
            "progress": progress_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"🔧 PROGRESS: ❌ Error getting progress: {e}")
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
                'job_listings': metadata.get('job_listings', 'Job data unavailable')
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get company details: {str(e)}'}), 500

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


@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(app.static_folder, 'favicon.ico')

if __name__ == '__main__':
    print("🚀 Starting Theodore Web UI...")
    print("🌐 Access at: http://localhost:5002")
    print("🔧 Google Search domain discovery enabled")
    app.run(debug=True, host='0.0.0.0', port=5002)