#!/usr/bin/env python3
"""
Theodore V2 - Simplified Version
Removes complex dependencies to isolate the issue
"""

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Simple HTML template inline
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Theodore V2 - Simple</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .form-group { margin: 20px 0; }
        .form-input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .btn { padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .results { margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 5px; }
        .company-card { margin: 15px 0; padding: 15px; background: white; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>🚀 Theodore V2 - Simple Version</h1>
    <p>Fast company discovery & focused research</p>
    
    <div class="form-group">
        <label>Company Name or Website URL:</label>
        <input type="text" id="companyInput" class="form-input" placeholder="Enter company name or URL">
    </div>
    
    <div class="form-group">
        <label>Number of companies:</label>
        <select id="limitSelect" class="form-input">
            <option value="3">3 companies</option>
            <option value="5" selected>5 companies</option>
            <option value="7">7 companies</option>
        </select>
    </div>
    
    <button class="btn" onclick="discover()">🔍 Discover Similar Companies</button>
    
    <div id="results" class="results" style="display: none;">
        <h3>Discovery Results</h3>
        <div id="companies"></div>
    </div>
    
    <script>
        async function discover() {
            const input = document.getElementById('companyInput').value.trim();
            const limit = document.getElementById('limitSelect').value;
            
            if (!input) {
                alert('Please enter a company name or URL');
                return;
            }
            
            console.log('🔍 Starting discovery for:', input);
            
            try {
                const response = await fetch('/api/discover', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ input_text: input, limit: parseInt(limit) })
                });
                
                const result = await response.json();
                console.log('✅ Discovery result:', result);
                
                if (result.success) {
                    displayResults(result);
                } else {
                    alert('Discovery failed: ' + result.error);
                }
            } catch (error) {
                console.error('❌ Discovery error:', error);
                alert('Network error occurred');
            }
        }
        
        function displayResults(result) {
            const resultsDiv = document.getElementById('results');
            const companiesDiv = document.getElementById('companies');
            
            let html = `<p><strong>Found ${result.total_found} similar companies:</strong></p>`;
            
            result.similar_companies.forEach(company => {
                html += `
                    <div class="company-card">
                        <h4>${company.name}</h4>
                        <p><strong>Website:</strong> <a href="${company.website}" target="_blank">${company.website}</a></p>
                        <p><strong>Similarity:</strong> ${(company.similarity_score * 100).toFixed(0)}%</p>
                        <p><strong>Why similar:</strong> ${company.reasoning}</p>
                        <button class="btn" onclick="research('${company.name}', '${company.website}')">🔬 Research</button>
                    </div>
                `;
            });
            
            companiesDiv.innerHTML = html;
            resultsDiv.style.display = 'block';
        }
        
        async function research(name, website) {
            console.log('🔬 Starting research for:', name);
            
            try {
                const response = await fetch('/api/research', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ company_name: name, website_url: website })
                });
                
                const result = await response.json();
                console.log('✅ Research result:', result);
                
                if (result.success) {
                    alert(`Research completed for ${name}!\\n\\nAnalysis: ${result.analysis.substring(0, 200)}...`);
                } else {
                    alert('Research failed: ' + result.error);
                }
            } catch (error) {
                console.error('❌ Research error:', error);
                alert('Research network error occurred');
            }
        }
        
        console.log('🚀 Theodore V2 Simple loaded');
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/discover', methods=['POST'])
def discover():
    try:
        data = request.get_json()
        input_text = data.get('input_text', '').strip()
        limit = int(data.get('limit', 5))
        
        print(f"🔍 Discovery request: '{input_text}' (limit: {limit})")
        
        # Mock discovery results
        mock_companies = [
            {
                "name": "Google",
                "website": "https://www.google.com",
                "similarity_score": 0.92,
                "reasoning": "Large technology company with similar enterprise software offerings"
            },
            {
                "name": "Amazon", 
                "website": "https://www.amazon.com",
                "similarity_score": 0.88,
                "reasoning": "Major cloud services provider with AWS"
            },
            {
                "name": "Apple",
                "website": "https://www.apple.com",
                "similarity_score": 0.85,
                "reasoning": "Technology giant with enterprise and consumer products"
            },
            {
                "name": "Salesforce",
                "website": "https://www.salesforce.com", 
                "similarity_score": 0.82,
                "reasoning": "Enterprise software and cloud services provider"
            },
            {
                "name": "Oracle",
                "website": "https://www.oracle.com",
                "similarity_score": 0.79,
                "reasoning": "Enterprise software and database solutions"
            }
        ]
        
        result = {
            "success": True,
            "input_text": input_text,
            "similar_companies": mock_companies[:limit],
            "total_found": min(len(mock_companies), limit)
        }
        
        print(f"✅ Discovery completed: {result['total_found']} companies")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Discovery error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/research', methods=['POST'])
def research():
    try:
        data = request.get_json()
        company_name = data.get('company_name', '')
        website_url = data.get('website_url', '')
        
        print(f"🔬 Research request: {company_name} at {website_url}")
        
        # Mock research result
        result = {
            "success": True,
            "company_name": company_name,
            "website": website_url,
            "analysis": f"Mock analysis for {company_name}: This company operates in the technology sector with a focus on enterprise solutions. They serve businesses of various sizes and have a strong market presence. Their website at {website_url} showcases their product offerings and company culture."
        }
        
        print(f"✅ Research completed for {company_name}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Research error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Theodore V2 Simple on http://localhost:8080")
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=False,
        use_reloader=False
    )