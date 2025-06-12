"""
Theodore V2 Application
Fast discovery with URL detection and focused research
"""

import os
import logging
from flask import Flask, request, jsonify, render_template, Response
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import V2 components
from src.v2_discovery import V2DiscoveryEngine
from src.v2_research import V2ResearchEngineSync
from src.bedrock_client import BedrockClient
from src.gemini_client import GeminiClient
from src.models import CompanyIntelligenceConfig
from src.progress_logger import progress_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize AI clients and V2 engines
config = CompanyIntelligenceConfig()

try:
    # Force Bedrock for stability (Gemini having issues)
    ai_client = BedrockClient(config)
    logger.info("✅ Using AWS Bedrock for V2 Theodore")
        
except Exception as e:
    logger.error(f"❌ Failed to initialize AI client: {e}")
    raise

# Initialize V2 engines
discovery_engine = V2DiscoveryEngine(ai_client)
research_engine = V2ResearchEngineSync(ai_client)

logger.info("🚀 Theodore V2 Application initialized successfully")

@app.route('/')
def index():
    """Main page"""
    return render_template('v2_index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "2.0",
        "ai_client": ai_client.__class__.__name__,
        "discovery_engine": "V2DiscoveryEngine",
        "research_engine": "V2ResearchEngineSync"
    })

@app.route('/api/v2/discover', methods=['POST'])
def v2_discover():
    """
    V2 Discovery endpoint
    Handles both company names and URLs
    """
    try:
        data = request.get_json()
        input_text = data.get('input_text', '').strip()
        limit = int(data.get('limit', 5))
        
        if not input_text:
            return jsonify({
                "success": False,
                "error": "Input text is required"
            }), 400
        
        logger.info(f"🔍 V2 Discovery request: '{input_text}' (limit: {limit})")
        
        # Use real V2 discovery engine
        result = discovery_engine.discover_similar_companies(input_text, limit)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ V2 Discovery error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v2/research/start', methods=['POST'])
def v2_research_start():
    """
    V2 Research endpoint - Start research job and return job_id immediately
    """
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        website_url = data.get('website_url', '').strip()
        
        if not company_name or not website_url:
            return jsonify({
                "success": False,
                "error": "Company name and website URL are required"
            }), 400
        
        logger.info(f"🔬 V2 Research request: {company_name} at {website_url}")
        
        # Create job_id for progress tracking
        from src.progress_logger import start_company_processing
        job_id = start_company_processing(company_name)
        
        logger.info(f"🔬 Started research job {job_id} for {company_name}")
        
        # Start research in background thread
        import threading
        def run_research():
            try:
                result = research_engine.research_company(company_name, website_url, job_id)
                # Store result in a way the frontend can retrieve it
                # For now, the progress logger will track completion
                logger.info(f"✅ Background research completed for {company_name}")
            except Exception as e:
                logger.error(f"❌ Background research failed for {company_name}: {e}")
        
        research_thread = threading.Thread(target=run_research)
        research_thread.start()
        
        # Return job_id immediately so frontend can start polling
        return jsonify({
            "success": True,
            "job_id": job_id,
            "company_name": company_name,
            "website": website_url,
            "message": "Research started",
            "status": "started"
        })
        
    except Exception as e:
        logger.error(f"❌ V2 Research start error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v2/research', methods=['POST'])
def v2_research():
    """
    V2 Research endpoint - Legacy synchronous version
    Focused research for a single company
    """
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        website_url = data.get('website_url', '').strip()
        
        if not company_name or not website_url:
            return jsonify({
                "success": False,
                "error": "Company name and website URL are required"
            }), 400
        
        logger.info(f"🔬 V2 Research request: {company_name} at {website_url}")
        
        # Create job_id for progress tracking
        from src.progress_logger import start_company_processing
        job_id = start_company_processing(company_name)
        
        logger.info(f"🔬 Started research job {job_id} for {company_name}")
        
        # Use real V2 research engine with job_id
        result = research_engine.research_company(company_name, website_url, job_id)
        
        # Add job_id to response so frontend can track it
        if isinstance(result, dict):
            result['job_id'] = job_id
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ V2 Research error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/progress/current')
def get_current_job_progress():
    """Get progress for currently running job"""
    try:
        job_id = request.args.get('job_id')
        if job_id:
            progress_data = progress_logger.get_progress(job_id)
        else:
            progress_data = progress_logger.get_current_job_progress()
            
        if progress_data:
            return jsonify({
                "success": True,
                "progress": progress_data
            })
        else:
            return jsonify({
                "success": False,
                "message": "No active job found"
            })
            
    except Exception as e:
        logger.error(f"Progress check error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/progress/all')
def get_all_job_progress():
    """Get all progress data"""
    try:
        all_progress = progress_logger.get_all_progress()
        return jsonify({
            "success": True,
            "progress": all_progress
        })
    except Exception as e:
        logger.error(f"All progress error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v2/validate-url', methods=['POST'])
def validate_url():
    """Validate if input text is a URL"""
    try:
        data = request.get_json()
        input_text = data.get('input_text', '').strip()
        
        is_url = discovery_engine.is_url(input_text)
        
        return jsonify({
            "success": True,
            "is_url": is_url,
            "input_text": input_text
        })
        
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v2/save-to-index', methods=['POST'])
def save_to_index():
    """Save researched company data to Pinecone index"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        research_data = data.get('research_data')
        
        if not company_name:
            return jsonify({
                "success": False,
                "error": "Company name is required"
            }), 400
        
        logger.info(f"💾 Saving {company_name} to Pinecone index")
        
        # Get research data - try multiple sources
        company_data = None
        
        # Method 1: Use provided research_data
        if research_data:
            logger.info("📋 Using provided research data")
            company_data = research_data
        else:
            # Method 2: Look for recent research in progress logger
            logger.info(f"🔍 Looking for recent research data for {company_name}")
            try:
                # Get all progress data and find the most recent for this company
                progress_data = progress_logger.get_all_progress()
                company_data = None
                
                for job_id, job_progress in progress_data.items():
                    if (job_progress.get('company_name', '').lower() == company_name.lower() and 
                        job_progress.get('status') == 'completed' and
                        'results' in job_progress):
                        company_data = job_progress['results']
                        logger.info(f"✅ Found research data in progress logger for job {job_id}")
                        break
                        
            except Exception as e:
                logger.warning(f"⚠️ Could not retrieve from progress logger: {e}")
        
        if not company_data:
            # Method 3: Perform fresh research
            logger.info(f"🔬 No existing data found, performing fresh research for {company_name}")
            try:
                # Extract website from company_data if available, otherwise use default
                website_url = company_data.get('website') if company_data else f"https://{company_name.lower().replace(' ', '')}.com"
                
                research_result = research_engine.research_company(company_name, website_url, None)
                if research_result and research_result.get('success'):
                    company_data = research_result
                    logger.info("✅ Fresh research completed successfully")
                else:
                    raise Exception("Fresh research failed")
                    
            except Exception as e:
                logger.error(f"❌ Fresh research failed: {e}")
                return jsonify({
                    "success": False,
                    "error": f"No research data available for {company_name} and fresh research failed: {str(e)}"
                }), 400
        
        # Now we have company_data, let's save it to Pinecone
        try:
            from src.models import CompanyData
            from src.pinecone_client import PineconeClient
            import os
            import uuid
            
            # Initialize Pinecone client
            pinecone_client = PineconeClient(
                config=config,
                api_key=os.getenv('PINECONE_API_KEY'),
                environment=os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
                index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
            )
            
            # Convert research data to CompanyData model
            company_obj = CompanyData(
                id=company_data.get('id') or str(uuid.uuid4()),
                name=company_data.get('company_name', company_name),
                website=company_data.get('website', ''),
                industry=company_data.get('industry', ''),
                business_model=company_data.get('business_model', ''),
                target_market=company_data.get('target_market', ''),
                company_size=company_data.get('company_size', ''),
                funding_status=company_data.get('funding_status', '')
            )
            
            # Add all the detailed research fields
            if 'ai_summary' in company_data:
                company_obj.ai_summary = company_data['ai_summary']
            if 'key_services' in company_data:
                company_obj.key_services = company_data['key_services']
            if 'tech_stack' in company_data:
                company_obj.tech_stack = company_data['tech_stack']
            if 'leadership_team' in company_data:
                company_obj.leadership_team = company_data['leadership_team']
            if 'competitive_advantages' in company_data:
                company_obj.competitive_advantages = company_data['competitive_advantages']
            if 'pain_points' in company_data:
                company_obj.pain_points = company_data['pain_points']
            if 'value_proposition' in company_data:
                company_obj.value_proposition = company_data['value_proposition']
            if 'company_description' in company_data:
                company_obj.company_description = company_data['company_description']
            if 'founding_year' in company_data:
                company_obj.founding_year = company_data['founding_year']
            if 'location' in company_data:
                company_obj.location = company_data['location']
            if 'employee_count_range' in company_data:
                company_obj.employee_count_range = company_data['employee_count_range']
            if 'company_culture' in company_data:
                company_obj.company_culture = company_data['company_culture']
            if 'social_media' in company_data:
                company_obj.social_media = company_data['social_media']
            if 'contact_info' in company_data:
                company_obj.contact_info = company_data['contact_info']
            if 'recent_news' in company_data:
                company_obj.recent_news = company_data['recent_news']
            if 'certifications' in company_data:
                company_obj.certifications = company_data['certifications']
            if 'partnerships' in company_data:
                company_obj.partnerships = company_data['partnerships']
            if 'awards' in company_data:
                company_obj.awards = company_data['awards']
            
            # Add enhanced similarity fields
            if 'company_stage' in company_data:
                company_obj.company_stage = company_data['company_stage']
            if 'tech_sophistication' in company_data:
                company_obj.tech_sophistication = company_data['tech_sophistication']
            if 'business_model_type' in company_data:
                company_obj.business_model_type = company_data['business_model_type']
            if 'geographic_scope' in company_data:
                company_obj.geographic_scope = company_data['geographic_scope']
            if 'decision_maker_type' in company_data:
                company_obj.decision_maker_type = company_data['decision_maker_type']
            if 'sales_complexity' in company_data:
                company_obj.sales_complexity = company_data['sales_complexity']
            
            # Add job listings data
            if 'has_job_listings' in company_data:
                company_obj.has_job_listings = company_data['has_job_listings']
            if 'job_listings_count' in company_data:
                company_obj.job_listings_count = company_data['job_listings_count']
            if 'job_listings_details' in company_data:
                company_obj.job_listings_details = company_data['job_listings_details']
            
            # Add key decision makers
            if 'key_decision_makers' in company_data:
                company_obj.key_decision_makers = company_data['key_decision_makers']
            
            # Generate embedding from comprehensive company content
            embedding_text = f"""
            Company: {company_obj.name}
            Website: {company_obj.website}
            Industry: {company_obj.industry}
            Business Model: {company_obj.business_model}
            Description: {company_obj.company_description or ''}
            Value Proposition: {company_obj.value_proposition or ''}
            Key Services: {' '.join(company_obj.key_services) if company_obj.key_services else ''}
            Tech Stack: {' '.join(company_obj.tech_stack) if company_obj.tech_stack else ''}
            Target Market: {company_obj.target_market}
            Company Size: {company_obj.company_size}
            Location: {company_obj.location or ''}
            AI Summary: {company_obj.ai_summary or ''}
            """.strip()
            
            # Generate embedding using AI client
            try:
                company_obj.embedding = ai_client.get_embeddings(embedding_text)
                logger.info(f"✅ Generated embedding for {company_name}")
            except Exception as e:
                logger.warning(f"⚠️ Embedding generation failed: {e}, proceeding without embedding")
                company_obj.embedding = None
            
            # Store in Pinecone
            success = pinecone_client.upsert_company(company_obj)
            
            if success:
                logger.info(f"✅ Successfully saved {company_name} to Pinecone index")
                return jsonify({
                    "success": True,
                    "message": f"{company_name} saved to index successfully",
                    "company_name": company_name,
                    "company_id": company_obj.id,
                    "fields_saved": len([k for k, v in vars(company_obj).items() if v is not None])
                })
            else:
                raise Exception("Pinecone upsert failed")
                
        except Exception as e:
            logger.error(f"❌ Pinecone storage failed: {e}")
            return jsonify({
                "success": False,
                "error": f"Failed to save to Pinecone: {str(e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Save to index error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/database', methods=['GET'])
def browse_database():
    """Browse companies in the Pinecone database"""
    try:
        from src.pinecone_client import PineconeClient
        import os
        
        # Initialize Pinecone client
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
            index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        # Get database stats
        stats = pinecone_client.get_index_stats()
        total_companies = stats.get('total_vectors', 0)
        
        # Get all companies using the Pinecone client
        companies = []
        try:
            # Query all vectors with metadata (get more than default)
            query_response = pinecone_client.index.query(
                vector=[0.0] * 1536,  # Dummy vector for metadata-only query
                top_k=200,  # Get more companies
                include_metadata=True,
                include_values=False
            )
            
            for match in query_response.matches:
                metadata = match.metadata or {}
                company_id = match.id
                
                companies.append({
                    "id": company_id,
                    "name": metadata.get('company_name', 'Unknown'),
                    "industry": metadata.get('industry', 'Unknown'),
                    "stage": metadata.get('company_stage', 'Unknown'),
                    "tech_level": metadata.get('tech_sophistication', 'Unknown'),
                    "business_model": metadata.get('business_model_type', metadata.get('business_model', 'Unknown')),
                    "geographic_scope": metadata.get('geographic_scope', 'Unknown'),
                    "website": metadata.get('website', 'Unknown'),
                    "target_market": metadata.get('target_market', 'Unknown'),
                    "company_size": metadata.get('company_size', 'Unknown'),
                    "last_updated": metadata.get('last_updated', ''),
                    "has_description": metadata.get('has_description', False)
                })
            
            # Sort by name for consistent display
            companies.sort(key=lambda x: x['name'].lower())
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to get companies: {e}")
            companies = []
        
        logger.info(f"📊 Database browser: {len(companies)} companies found")
        
        from datetime import datetime
        
        return jsonify({
            "success": True,
            "total_companies": total_companies,
            "companies": companies,
            "database_stats": {"total_vectors": total_companies},
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Database browse error: {e}")
        return jsonify({
            "success": False,
            "error": f"Database browse failed: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Development server
    print("🚀 Starting Theodore V2 on http://localhost:5004")
    app.run(
        host='127.0.0.1',
        port=5004,
        debug=True,
        use_reloader=True
    )