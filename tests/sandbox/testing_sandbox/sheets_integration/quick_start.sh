#!/bin/bash

# Quick start script for Google Sheets integration testing

echo "🚀 Theodore Google Sheets Integration - Quick Start"
echo "================================================="

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Please run this script from the sheets_integration directory"
    exit 1
fi

echo ""
echo "📋 Choose authentication method:"
echo ""
echo "1. Service Account (Recommended - No browser needed!):"
echo "   python3 cli_tools/test_service_auth.py"
echo ""
echo "2. OAuth2 (Requires browser):"
echo "   python3 cli_tools/test_auth.py"
echo ""
echo "📋 Available commands:"
echo ""
echo "Service Account Commands (Recommended):"
echo "  - Test authentication: python3 cli_tools/test_service_auth.py"
echo "  - Batch processing: python3 cli_tools/test_batch_service.py"
echo ""
echo "OAuth2 Commands (Legacy):"
echo "  - Test authentication: python3 cli_tools/test_auth.py"
echo "  - Create sheet structure: python3 cli_tools/test_sheet_creation.py"
echo "  - Batch processing: python3 cli_tools/test_batch_processing.py"
echo ""
echo "Other:"
echo "  - Start test server: python3 test_server.py"
echo "  - View spreadsheet: https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit"
echo ""
echo "================================================="
echo ""
echo "Starting with service account test (recommended)..."
echo ""

python3 cli_tools/test_service_auth.py