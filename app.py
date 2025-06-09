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
                bedrock_client=pipeline.bedrock_client,
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
                from src.research_manager import ResearchManager
                pipeline.research_manager = ResearchManager(
                    intelligent_scraper=pipeline.scraper,
                    pinecone_client=pipeline.pinecone_client,
                    bedrock_client=pipeline.bedrock_client
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
    try:
        data = request.get_json()
        company_data = data.get('company', {})
        
        if not company_data or not company_data.get('name'):
            return jsonify({
                "error": "Company data is required",
                "company": {}
            }), 400
        
        # Check if pipeline is available
        if not pipeline:
            return jsonify({
                "error": "Theodore pipeline not available",
                "company": {}
            }), 500
        
        try:
            # Initialize enhanced discovery with scraper
            from src.simple_enhanced_discovery import SimpleEnhancedDiscovery
            
            enhanced_discovery = SimpleEnhancedDiscovery(
                bedrock_client=pipeline.bedrock_client,
                pinecone_client=pipeline.pinecone_client,
                scraper=pipeline.scraper
            )
            
            # Research the company on-demand
            researched_company = enhanced_discovery.research_company_on_demand(company_data)
            
            return jsonify({
                "success": True,
                "company": researched_company,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            print(f"Research error: {e}")
            return jsonify({
                "error": f"Research failed: {str(e)}",
                "company": company_data
            }), 500
            
    except Exception as e:
        print(f"Research endpoint error: {e}")
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "company": {}
        }), 500

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
            from src.research_manager import ResearchManager
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
            from src.research_manager import ResearchManager
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
            from src.research_manager import ResearchManager
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
            from src.research_manager import ResearchManager
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
            from src.research_manager import ResearchManager
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
            from src.research_manager import ResearchManager
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
            from src.research_manager import ResearchManager
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
            from src.research_manager import ResearchManager
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
            from src.research_manager import ResearchManager
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
            from src.research_manager import ResearchManager
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
            from src.research_manager import ResearchManager
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
        from src.similarity_prompts import INDUSTRY_CLASSIFICATION_FROM_RESEARCH_PROMPT
        
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
    app.run(debug=True, host='0.0.0.0', port=5002)