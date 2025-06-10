#!/usr/bin/env python3
from flask import Flask
import threading
import webbrowser
import time

app = Flask(__name__)

@app.route('/')
def hello():
    return "<h1>✅ Flask is working!</h1><p>Port: 8080</p>"

if __name__ == '__main__':
    print("🚀 Starting on http://localhost:8080")
    
    # Try to open browser automatically
    def open_browser():
        time.sleep(1)
        webbrowser.open('http://localhost:8080')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=False,  # No reloader
        use_reloader=False
    )