#!/usr/bin/env python3
"""
Check Google Sheet Tabs
Find available tabs and their data
"""

import pandas as pd
import requests
from urllib.parse import urlparse, parse_qs

# Try different GIDs to find the details tab
SHEET_BASE_URL = "https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/export?format=csv&gid="

# Common GIDs to try
GIDS_TO_TRY = [
    "0",           # Usually first tab
    "1",           # Second tab
    "2",           # Third tab  
    "1485147716",  # The one we tried
    "123456789",   # Random test
]

def try_fetch_tab(gid):
    """Try to fetch a specific tab"""
    url = SHEET_BASE_URL + gid
    try:
        print(f"🔍 Trying GID {gid}...")
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()
        
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        print(f"✅ GID {gid}: {len(df)} rows, {len(df.columns)} columns")
        print(f"   Columns: {list(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}")
        
        # Check for enhanced data indicators
        enhanced_indicators = [
            'analysis', 'summary', 'classification', 'enhanced', 'detailed',
            'intelligence', 'extracted', 'business_model', 'saas', 'ai'
        ]
        
        enhanced_columns = []
        for col in df.columns:
            if any(indicator in col.lower() for indicator in enhanced_indicators):
                enhanced_columns.append(col)
        
        if enhanced_columns:
            print(f"   🎯 Enhanced data columns found: {enhanced_columns[:5]}")
        
        return df, True
        
    except Exception as e:
        print(f"❌ GID {gid}: {e}")
        return None, False

def main():
    """Check all tabs"""
    print("🔍 CHECKING GOOGLE SHEET TABS")
    print("=" * 50)
    
    found_tabs = {}
    
    for gid in GIDS_TO_TRY:
        df, success = try_fetch_tab(gid)
        if success:
            found_tabs[gid] = df
    
    print(f"\n📊 SUMMARY:")
    print(f"Found {len(found_tabs)} accessible tabs")
    
    if len(found_tabs) >= 2:
        print(f"\n🎯 COMPARING TABS FOR ENHANCEMENT DATA:")
        gids = list(found_tabs.keys())
        
        tab1_gid, tab2_gid = gids[0], gids[1]
        tab1_df = found_tabs[tab1_gid]
        tab2_df = found_tabs[tab2_gid]
        
        print(f"\nTab 1 (GID {tab1_gid}): {len(tab1_df)} rows, {len(tab1_df.columns)} columns")
        print(f"Tab 2 (GID {tab2_gid}): {len(tab2_df)} rows, {len(tab2_df.columns)} columns")
        
        # Check which has more data/columns
        if len(tab2_df.columns) > len(tab1_df.columns):
            print(f"✅ Tab 2 (GID {tab2_gid}) appears to have enhanced data")
            enhanced_df = tab2_df
            enhanced_gid = tab2_gid
            basic_df = tab1_df
            basic_gid = tab1_gid
        else:
            print(f"✅ Tab 1 (GID {tab1_gid}) appears to have enhanced data")
            enhanced_df = tab1_df
            enhanced_gid = tab1_gid
            basic_df = tab2_df
            basic_gid = tab2_gid
        
        # Show sample data from enhanced tab
        print(f"\n📋 Sample enhanced columns from GID {enhanced_gid}:")
        for i, col in enumerate(enhanced_df.columns[:20]):
            sample_data = enhanced_df[col].dropna().iloc[0] if not enhanced_df[col].dropna().empty else "No data"
            print(f"   {i+1:2d}. {col}: {str(sample_data)[:50]}...")
        
        return basic_df, enhanced_df, basic_gid, enhanced_gid
    
    else:
        print("❌ Could not find both basic and enhanced tabs")
        return None, None, None, None

if __name__ == "__main__":
    main()