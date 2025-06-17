#!/usr/bin/env python3
"""
OAuth2 Setup Instructions for Google Sheets Integration
"""

print("""
🔐 Google Sheets OAuth2 Setup Instructions
==========================================

The current OAuth2 credentials are configured as a "Web application" type,
but we need "Desktop application" credentials for command-line tools.

To fix the "redirect_uri_mismatch" error:

Option 1: Create Desktop Application Credentials (Recommended)
-------------------------------------------------------------
1. Go to: https://console.cloud.google.com/apis/credentials
2. Select your project: theodore-462403
3. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
4. Choose "Desktop app" as the Application type
5. Name it: "Theodore Sheets CLI"
6. Click "CREATE"
7. Download the JSON file
8. Replace the current credentials file with the new one

Option 2: Use Service Account (Alternative)
-------------------------------------------
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "+ CREATE CREDENTIALS" → "Service account"
3. Name: "theodore-sheets-service"
4. Grant role: "Editor" or "Owner"
5. Create and download JSON key
6. Share your Google Sheet with the service account email

Option 3: Add Redirect URIs to Current Web App (Not Recommended)
---------------------------------------------------------------
Since this is a web app credential, you would need to add ALL possible
redirect URIs that the library might use:
- http://localhost:8080/
- http://localhost:8080
- http://localhost:8090/
- http://localhost:8090
- And many more...

This is not practical for desktop applications.

Current Credential Details:
--------------------------
Client ID: 1096944990043-5u1eohnobc583lvueqr2cvfvm9tcjc3p.apps.googleusercontent.com
Project: theodore-462403
Type: Web application (this is the problem)

📋 Next Steps:
--------------
1. Create new Desktop app credentials following Option 1
2. Save the file as 'credentials_desktop.json' in this directory
3. Update the code to use the new credentials file

Would you like me to create a service account authentication script instead?
""")