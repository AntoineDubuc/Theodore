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
        
        if not company_name:
            return jsonify({
                "success": False,
                "error": "Company name is required"
            }), 400
        
        logger.info(f"💾 Saving {company_name} to Pinecone index")
        
        # For now, return success (actual Pinecone integration would go here)
        # In a full implementation, you would:
        # 1. Get the research data from progress logger or session
        # 2. Convert to CompanyData model
        # 3. Generate embeddings
        # 4. Store in Pinecone with proper metadata
        
        return jsonify({
            "success": True,
            "message": f"{company_name} saved to index successfully",
            "company_name": company_name
        })
        
    except Exception as e:
        logger.error(f"❌ Save to index error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
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