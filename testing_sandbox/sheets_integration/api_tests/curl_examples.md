# Google Sheets API Test Examples

Use these curl commands to test the API endpoints after starting the test server.

## Start the test server first:
```bash
cd testing_sandbox/sheets_integration
python test_server.py
```

## 1. Health Check
```bash
curl http://localhost:5555/test/health
```

## 2. Validate Authentication
```bash
curl -X POST http://localhost:5555/test/auth/validate \
  -H "Content-Type: application/json" \
  -d '{"sheet_id": "1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk"}'
```

## 3. Create Dual-Sheet Structure
```bash
curl -X POST http://localhost:5555/test/sheets/create \
  -H "Content-Type: application/json" \
  -d '{"sheet_id": "1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk"}'
```

## 4. Validate Sheet Structure
```bash
curl -X POST http://localhost:5555/test/sheets/validate \
  -H "Content-Type: application/json" \
  -d '{"sheet_id": "1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk"}'
```

## 5. Start Batch Processing
```bash
curl -X POST http://localhost:5555/test/sheets/process \
  -H "Content-Type: application/json" \
  -d '{
    "sheet_id": "1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk",
    "concurrency": 3,
    "update_interval": 1
  }'
```

## 6. Check Job Status
```bash
# Replace JOB_ID with the actual job ID returned from the process endpoint
curl http://localhost:5555/test/sheets/status/JOB_ID
```

## 7. Validate Field Mapping
```bash
curl http://localhost:5555/test/field-mapping/validate
```

## 8. Test Mock Research
```bash
curl -X POST http://localhost:5555/test/company/mock-research \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Anthropic"}'
```

## Using jq for pretty output:
```bash
# Install jq if needed: brew install jq
curl http://localhost:5555/test/health | jq .
```

## Test Workflow:
1. Start the server
2. Run health check
3. Validate authentication (will open browser for OAuth if needed)
4. Create sheet structure
5. Validate the structure
6. Add some companies to the sheet manually
7. Start batch processing
8. Monitor progress in the Google Sheet