# Theodore Startup Guide

**The CORRECT way to start Theodore Web UI**

## ✅ Working Startup Method

### 1. Navigate to Theodore Directory
```bash
cd /Users/antoinedubuc/Desktop/AI_Goodies/Theodore
```

### 2. Start the Application (Background Mode)
```bash
nohup python3 app.py > app.log 2>&1 & echo $!
```

This command:
- `nohup` - Runs the process immune to hangups
- `python3 app.py` - Starts the Flask application
- `> app.log 2>&1` - Redirects all output to app.log
- `&` - Runs in background
- `echo $!` - Shows the process ID

### 3. Verify Startup (Wait 10 seconds)
```bash
sleep 10 && tail -10 app.log
```

Look for these success indicators:
```
✅ Theodore pipeline initialized successfully
🚀 Starting Theodore Web UI...
🌐 Access at: http://localhost:5002
* Running on http://127.0.0.1:5002
* Running on http://192.168.0.176:5002
* Debugger is active!
```

### 4. Test the Application
```bash
# Test main endpoint
curl -I http://localhost:5002/

# Test settings API
curl -s http://localhost:5002/api/settings | jq '.models'
```

### 5. Access URLs
- **Main Dashboard**: http://localhost:5002/
- **Settings Page**: http://localhost:5002/settings
- **API Health**: http://localhost:5002/api/health

## 🛑 Stop the Application
```bash
# Find the process ID
ps aux | grep "python3 app.py" | grep -v grep

# Kill by PID (use the number from step 2)
kill [PID_NUMBER]

# Or kill all Python processes (use with caution)
pkill -f "python3 app.py"
```

## 🔧 Troubleshooting

### Problem: Port Already in Use
```bash
# Check what's using port 5002
lsof -i :5002

# Kill the process using the port
kill -9 [PID]
```

### Problem: Import Errors
```bash
# Test imports
python3 -c "import app; print('Import successful')"

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

### Problem: Environment Variables Missing
```bash
# Check required environment variables
echo "AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID"
echo "GEMINI_API_KEY: $GEMINI_API_KEY"
echo "PINECONE_API_KEY: $PINECONE_API_KEY"
```

### Problem: Application Won't Start
1. Check syntax: `python3 -m py_compile app.py`
2. Check dependencies: `pip3 list | grep -E "(flask|pinecone|google)"` 
3. Check working directory: `pwd` (should be in Theodore folder)
4. Check logs: `tail -50 app.log`

## 📊 Monitoring the Application

### View Live Logs
```bash
tail -f app.log
```

### Check Application Status
```bash
# Quick health check
curl -s http://localhost:5002/api/health | jq '.'

# Detailed system info
curl -s http://localhost:5002/api/settings | jq '.system_status'
```

### Monitor Performance
```bash
# Check memory usage
ps aux | grep "python3 app.py"

# Check network connections
netstat -an | grep :5002
```

## 🎯 Success Indicators

When Theodore starts correctly, you should see:

1. **Console Output**:
   ```
   ✅ Theodore pipeline initialized successfully
   🚀 Starting Theodore Web UI...
   🌐 Access at: http://localhost:5002
   ```

2. **API Response** (curl test):
   ```json
   {
     "models": {
       "bedrock_available": true,
       "gemini_available": true,
       "openai_available": true
     }
   }
   ```

3. **Web Interface**: 
   - http://localhost:5002/ loads with the Theodore dashboard
   - http://localhost:5002/settings shows the configuration page

## 🚀 Alternative Startup Methods

### Development Mode (Foreground)
```bash
python3 app.py
```
- Use Ctrl+C to stop
- Good for development/debugging
- Blocks terminal

### Production Mode (with gunicorn)
```bash
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5002 app:app
```
- More stable for production
- Better performance
- Multiple workers

## 📝 Environment Setup Checklist

Before starting Theodore, ensure:

- [ ] In correct directory (`/Users/antoinedubuc/Desktop/AI_Goodies/Theodore`)
- [ ] Python 3 installed (`python3 --version`)
- [ ] Dependencies installed (`pip3 install -r requirements.txt`)
- [ ] Environment variables set (AWS, Gemini, Pinecone API keys)
- [ ] Port 5002 available (`lsof -i :5002` shows nothing)
- [ ] No existing Theodore processes running

## 🎉 Quick Start (One-Liner)

```bash
cd /Users/antoinedubuc/Desktop/AI_Goodies/Theodore && nohup python3 app.py > app.log 2>&1 & sleep 5 && curl -I http://localhost:5002/ && echo "Theodore started successfully!"
```

This command:
1. Changes to Theodore directory
2. Starts the app in background
3. Waits 5 seconds for startup
4. Tests the endpoint
5. Confirms success

---

**Remember**: The key is using `nohup` with background execution (`&`) and redirecting output to a log file. This prevents the terminal from hanging and allows proper monitoring.