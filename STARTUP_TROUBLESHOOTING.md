# 🔧 Theodore Startup Troubleshooting Guide

The app has been fixed but may need manual intervention to start. Follow these steps:

## 🎯 Step 1: Test Minimal App First

Start with the minimal version to test if Flask works:

```bash
cd /Users/antoinedubuc/Desktop/AI_Goodies/Theodore
python3 minimal_app.py
```

If this works, you'll see:
- "🧪 Starting MINIMAL Theodore app..."
- Access http://localhost:5002 to confirm basic Flask is working

## 🎯 Step 2: Check Port Usage

If the minimal app doesn't start, check if port 5002 is in use:

```bash
lsof -i :5002
# If something is using port 5002, kill it:
kill -9 <PID>
```

## 🎯 Step 3: Test Full App

Once minimal app works, try the full app:

```bash
python3 app.py
```

## 🎯 Step 4: Common Issues & Solutions

### A) Import Errors
If you see import errors, check that all required packages are installed:
```bash
pip install -r requirements.txt
```

### B) Permission Errors
If you get permission errors:
```bash
chmod +x *.py
```

### C) Environment Variables Missing
If the app complains about missing environment variables, check your `.env` file:
```bash
cat .env
```

Should contain:
```
PINECONE_API_KEY=your_key_here
PINECONE_INDEX_NAME=theodore-companies
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
GEMINI_API_KEY=your_gemini_key
```

### D) Python Path Issues
If you get module import errors:
```bash
export PYTHONPATH=/Users/antoinedubuc/Desktop/AI_Goodies/Theodore:$PYTHONPATH
python3 app.py
```

## 🎯 Step 5: Alternative Startup Methods

### Method A: Direct Python Module
```bash
python3 -m app
```

### Method B: With Explicit Path
```bash
PYTHONPATH=. python3 app.py
```

### Method C: Using Full Path
```bash
/usr/bin/python3 /Users/antoinedubuc/Desktop/AI_Goodies/Theodore/app.py
```

## 🎯 Step 6: Debug Output

If the app starts but crashes immediately, run it with debug output:

```bash
python3 -u app.py 2>&1 | tee startup_debug.log
```

This will show all startup messages and save them to `startup_debug.log`.

## 🎯 Expected Success Output

When working correctly, you should see:

```
🔧 DIAGNOSTIC MODE: Testing each pipeline component individually...
🔍 Stage 1: Checking environment variables...
   ✅ PINECONE_API_KEY: Set
   ✅ PINECONE_INDEX_NAME: Set
   [... component tests ...]
✅ FULL PIPELINE CREATED SUCCESSFULLY!
✅ Startup pipeline initialization successful
🚀 Starting Theodore Web UI...
🌐 Access at: http://localhost:5002
```

Then you can access:
- **Main UI**: http://localhost:5002
- **Diagnostic**: http://localhost:5002/diagnostic
- **Health Check**: http://localhost:5002/api/health

## 🆘 If Nothing Works

If all methods fail, the issue might be:

1. **Python environment** - Try using a different Python version
2. **File permissions** - Check that all files are readable
3. **System dependencies** - Some packages might be missing
4. **Port conflicts** - Try changing the port in app.py from 5002 to 5003

The minimal app should work in most cases and will help identify if the issue is with Flask basics or Theodore-specific components.