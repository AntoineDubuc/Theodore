# Service Account Setup for Theodore Google Sheets Integration

## 🎯 Overview
Service Account authentication is the best approach for Theodore's batch processing needs:
- No browser interaction required
- Works on servers and automated environments
- Persistent authentication (no token refresh needed)
- Industry standard for server-side applications

## 📋 Step-by-Step Setup Instructions

### Step 1: Create Service Account

1. **Go to Google Cloud Console**
   - Navigate to: https://console.cloud.google.com/iam-admin/serviceaccounts
   - Make sure project `theodore-462403` is selected (top left)

2. **Create New Service Account**
   - Click `+ CREATE SERVICE ACCOUNT` button
   - Fill in:
     - **Service account name**: `theodore-sheets-processor`
     - **Service account ID**: `theodore-sheets-processor` (auto-fills)
     - **Description**: `Service account for Theodore batch processing Google Sheets`
   - Click `CREATE AND CONTINUE`

3. **Grant Permissions**
   - In "Grant this service account access to project" section
   - Click `Select a role` dropdown
   - Search for and select: `Google Sheets API > Google Sheets API Editor`
   - Click `CONTINUE`
   - Click `DONE` (skip the optional 3rd step)

### Step 2: Create and Download Key

1. **Access Service Account**
   - You'll see your new service account in the list
   - Click on `theodore-sheets-processor@theodore-462403.iam.gserviceaccount.com`

2. **Generate Key**
   - Go to `KEYS` tab
   - Click `ADD KEY` → `Create new key`
   - Select `JSON` format
   - Click `CREATE`
   - A JSON file will download automatically

3. **Save Key File**
   - Rename the downloaded file to: `theodore-service-account.json`
   - Move it to: `/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/testing_sandbox/sheets_integration/`
   - Place it in the sheets_integration folder (NOT in a subfolder)

### Step 3: Share Your Google Sheet

1. **Open Your Sheet**
   - Go to: https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit

2. **Share with Service Account**
   - Click the `Share` button (top right)
   - In the "Add people and groups" field, enter:
     ```
     theodore-sheets-processor@theodore-462403.iam.gserviceaccount.com
     ```
   - Set permission to `Editor`
   - Uncheck "Notify people" (service accounts don't have email)
   - Click `Share`

### Step 4: Test the Setup

Run the test script to verify everything works:

```bash
cd /Users/antoinedubuc/Desktop/AI_Goodies/Theodore/testing_sandbox/sheets_integration
python3 cli_tools/test_service_auth.py
```

## 🔒 Security Best Practices

1. **Never commit the service account key to Git**
   - Add to `.gitignore`: `**/theodore-service-account.json`
   - Add: `**/*service-account*.json`

2. **Protect the key file**
   - Set restrictive permissions: `chmod 600 service_account_key.json`
   - Store in secure location

3. **Rotate keys periodically**
   - Delete old keys from Google Cloud Console
   - Generate new keys every 90 days

4. **Use environment variables in production**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service_account_key.json"
   ```

## 📊 What Happens Next

Once setup is complete:
1. No more OAuth2 browser prompts
2. Authentication happens automatically
3. Can run batch processing unattended
4. Works on servers without GUI
5. Process all 6000 companies without intervention

## 🚨 Troubleshooting

**Error: "Permission denied"**
- Make sure you shared the sheet with the service account email
- Verify the service account has Editor permission

**Error: "File not found"**
- Check the service_account_key.json path
- Ensure the credentials folder exists

**Error: "Invalid grant"**
- The service account email might be wrong
- Re-download the key file from Google Cloud Console

## ✅ Success Indicators

When everything is set up correctly:
- No browser windows open
- Authentication is instant
- Can access and modify the Google Sheet
- Batch processing runs unattended