# Theodore Settings Page Overview

The settings page provides comprehensive visibility into Theodore's configuration, performance, and cost structure.

## 🔗 Access
- URL: `http://localhost:5002/settings`
- Navigation: Available from the main dashboard

## 📋 Features

### 🤖 AI Model Configuration
- **Primary Analysis Model**: Amazon Nova Pro (6x cost reduction)
- **Enhanced Extraction Model**: Gemini 2.5 Flash Preview
- **Fallback Model**: GPT-4o Mini
- **Status Indicators**: Real-time connection status for each model
- **Test Connections**: Button to verify all AI model connectivity

### 💰 Cost Estimates & Analysis
- **Per Company Cost**: $0.0045 (enhanced extraction)
- **Batch Processing Costs**: 
  - 10 companies: $0.05
  - 100 companies: $0.47  
  - 400 companies: $1.89
- **Cost Breakdown**:
  - Primary Analysis: $0.0042
  - Enhanced Extraction: +$0.0002
  - Pattern Extraction: Free
  - Embeddings: ~$0.0001
- **Real-time Recalculation**: Updates costs based on current usage

### 📝 AI Prompt Configuration
**Expandable Prompt Editors:**

1. **Company Analysis Prompt**
   - Focuses on industry, business model, company size
   - Extracts structured business intelligence
   - Returns JSON with key fields

2. **Page Selection Prompt**  
   - Enhanced LLM prompt targeting missing data
   - Prioritizes contact, about, team pages
   - Optimized for location, founding year, employee count

3. **Enhanced Extraction Prompt**
   - Pattern-based field extraction
   - Targets specific data types (founding year, employee count, etc.)
   - Returns structured JSON

**Prompt Management:**
- ✏️ Edit prompts in real-time
- 💾 Save changes instantly
- 🔄 Reset to defaults
- 📥 Export prompts for backup

### 📊 System Status
- **Pinecone Database**: Connection status and index name
- **Companies Count**: Number of companies in database
- **Last Processing**: Recent activity timestamp
- **System Uptime**: Current session duration
- **Health Check**: Comprehensive system diagnostics

### 🔧 Extraction Settings
- **Scraping Timeout**: 25 seconds (adjustable)
- **Max Pages per Company**: 50 pages
- **Enhanced Extraction**: Enabled/Disabled toggle
- **Pattern Count**: Number of active extraction patterns (15)

### ⚡ Performance Metrics
- **Average Processing Time**: 45 seconds per company
- **Success Rate**: 75% (scraping success)
- **Field Extraction Rate**: 23% (target fields filled)
- **24h Processing**: Recent activity counter

## 🛠️ Interactive Features

### Model Testing
- Test all configured AI models
- Real-time connection verification
- Error reporting for failed connections

### Cost Recalculation
- Updates estimates based on current model pricing
- Integrates with the cost analysis system
- Shows impact of configuration changes

### System Health Check
- Tests all critical components:
  - Pipeline initialization
  - Pinecone database connection
  - AI model availability
- Overall health status indicator

### Configuration Export
- Export full system configuration as JSON
- Export prompts separately for version control
- Timestamped backup files

## 📈 Real-time Updates
- Settings refresh automatically when changed
- Toast notifications for all actions
- Loading indicators for longer operations
- Error handling with user-friendly messages

## 🎨 Design Features
- **Dark Theme**: Modern gradient design matching Theodore's interface
- **Responsive Layout**: Grid-based layout adapts to screen size
- **Expandable Sections**: Collapsible prompt editors save space
- **Status Indicators**: Color-coded dots for system health
- **Interactive Elements**: Hover effects and smooth animations

## 💡 Key Benefits

1. **Transparency**: Full visibility into costs and configuration
2. **Control**: Ability to modify prompts and settings
3. **Monitoring**: Real-time system health and performance
4. **Optimization**: Easy identification of improvement opportunities
5. **Debugging**: Comprehensive status information for troubleshooting

## 🔧 Technical Implementation

### Backend API Endpoints
```
GET  /api/settings                    # Get all settings
POST /api/settings/test-models        # Test AI connections  
POST /api/settings/recalculate-costs  # Update cost estimates
POST /api/settings/save-prompt        # Save prompt changes
POST /api/settings/reset-prompts      # Reset to defaults
POST /api/settings/health-check       # System diagnostics
```

### Frontend Technology
- Pure JavaScript (no frameworks)
- CSS Grid for responsive layout
- Fetch API for backend communication
- Local state management
- Toast notifications system

### Integration Points
- Connects to cost analysis system (`cost_analysis.py`)
- Reads current prompts from extraction system
- Monitors pipeline and database status
- Tracks performance metrics

## 🚀 Usage Scenarios

1. **Initial Setup**: Verify all models are connected and configured
2. **Cost Planning**: Estimate costs for different batch sizes
3. **Prompt Optimization**: Modify and test extraction prompts
4. **Performance Monitoring**: Track success rates and processing times
5. **System Debugging**: Diagnose issues with health checks
6. **Configuration Backup**: Export settings before major changes

The settings page serves as Theodore's "mission control" - providing complete oversight and control over the AI-powered company intelligence system.