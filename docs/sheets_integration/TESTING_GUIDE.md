# 🧪 Theodore Google Sheets Testing Guide

## ⚠️ IMPORTANT: Testing Safety

We are in **TESTING MODE** - DO NOT process all 6000 companies!

### Testing Limits Implemented:
- **Max companies per test**: 2
- **Concurrency**: 2 (processes 2 at a time)
- **Single company test**: Available for safest testing

## 📋 Testing Steps (In Order)

### 1. Test Authentication First
```bash
cd testing_sandbox/sheets_integration
python3 cli_tools/test_service_auth.py
```
This will:
- Verify the service account file exists
- Test authentication
- Show which companies would be processed
- NOT process any companies

### 2. Test Single Company (SAFEST)
```bash
python3 cli_tools/test_single_company.py
```
This will:
- Process exactly ONE company
- Show you which company before processing
- Ask for confirmation
- Update the sheet with results

### 3. Test Batch Processing (2 Companies Max)
```bash
python3 cli_tools/test_batch_service.py
```
This will:
- Process maximum 2 companies
- Use concurrency of 2
- Show clear warnings about limits
- Ask for confirmation

## 🔍 What to Check After Testing

1. **Google Sheet Updates**:
   - Status column shows "completed" or "failed"
   - Progress column shows "100%" when done
   - Research Date populated
   - Industry, Stage, Tech Level filled in
   - "View Details" link works
   - Error Notes (if any failures)

2. **Details Tab**:
   - Headers added automatically
   - Complete research data populated
   - All 62+ fields filled where applicable

3. **Console Output**:
   - Processing logs
   - Success/failure messages
   - Rate of processing

## ⚠️ Before Full Production

When ready for full 6000 company processing:
1. Change `MAX_COMPANIES_FOR_TESTING` in test_batch_service.py
2. Increase `concurrency` to 10
3. Run on a server that can handle long processing
4. Monitor progress regularly

## 🛑 Stop Processing

If you need to stop:
- Press Ctrl+C in terminal
- Processing will stop gracefully
- Already processed companies remain completed
- Can resume later (processes only "pending" status)

## 📊 Expected Results

For 2 company test:
- Duration: ~2-4 minutes
- Both companies should complete
- Full data in both tabs
- No authentication prompts

## 🔧 Troubleshooting

**"Permission denied" error**:
- Make sure sheet is shared with service account email
- Check SERVICE_ACCOUNT_SETUP.md

**"File not found" error**:
- Verify theodore-service-account.json is in sheets_integration folder
- Not in a subfolder

**Companies not processing**:
- Check if they already have "completed" status
- Only "pending" or "failed" companies are processed