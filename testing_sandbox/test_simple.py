#!/usr/bin/env python3
"""
Simple test Flask app to debug basic functionality
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <html>
    <head><title>Theodore V2 Test</title></head>
    <body>
        <h1>🚀 Theodore V2 Test Page</h1>
        <p>If you can see this, Flask is working!</p>
        <p>Time: <span id="time"></span></p>
        <script>
            document.getElementById('time').textContent = new Date().toLocaleString();
        </script>
    </body>
    </html>
    """

@app.route('/api/test')
def test_api():
    return {"status": "success", "message": "API is working"}

if __name__ == '__main__':
    print("🧪 Starting simple test app on http://localhost:5005")
    print("📍 Visit: http://localhost:5005")
    print("🔧 API test: http://localhost:5005/api/test")
    app.run(
        host='127.0.0.1',
        port=5005,
        debug=True
    )