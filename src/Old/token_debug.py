# token_debug.py
"""
Debug token loading to see if .env file was updated properly
"""

import os
from dotenv import load_dotenv

def debug_token_loading():
    """Debug what tokens are actually being loaded"""
    
    print("🔍 TOKEN LOADING DEBUG")
    print("=" * 30)
    
    # Load .env file
    print("📁 Loading .env file...")
    load_result = load_dotenv(override=True)  # Force reload
    print(f"   Load result: {load_result}")
    
    # Get tokens
    access_token = os.getenv('NB_PA_TOKEN')
    refresh_token = os.getenv('NB_PA_TOKEN_REFRESH')
    nation_slug = os.getenv('NB_NATION_SLUG')
    client_id = os.getenv('NB_PA_ID')
    client_secret = os.getenv('NB_PA_SECRET')
    
    print(f"\n📋 LOADED TOKENS:")
    print(f"   Nation: {nation_slug}")
    print(f"   Access Token: {access_token[:20] + '...' if access_token else 'MISSING'}")
    print(f"   Access Length: {len(access_token) if access_token else 0}")
    print(f"   Refresh Token: {refresh_token[:10] + '...' if refresh_token else 'MISSING'}")  
    print(f"   Refresh Length: {len(refresh_token) if refresh_token else 0}")
    print(f"   Client ID: {client_id[:10] + '...' if client_id else 'MISSING'}")
    print(f"   Client Secret: {'Present' if client_secret else 'MISSING'}")
    
    # Test the current tokens directly
    print(f"\n🧪 TESTING CURRENT TOKENS DIRECTLY:")
    test_tokens_directly(access_token, nation_slug)
    
    # Check .env file contents
    print(f"\n📄 CHECKING .env FILE CONTENTS:")
    check_env_file_contents()

def test_tokens_directly(access_token: str, nation_slug: str):
    """Test tokens with direct HTTP request (not using our client)"""
    if not access_token or not nation_slug:
        print("❌ Missing access token or nation slug")
        return
    
    import requests
    
    url = f"https://{nation_slug}.nationbuilder.com/api/v2/signups"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    params = {'page[size]': 1}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Direct token test SUCCESSFUL!")
            data = response.json()
            if data.get('data'):
                print(f"   📊 Retrieved {len(data['data'])} signup(s)")
        else:
            print(f"   ❌ Direct token test FAILED!")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text[:200]}")
                
    except Exception as e:
        print(f"   💥 Request failed: {e}")

def check_env_file_contents():
    """Check what's actually in the .env file"""
    try:
        if os.path.exists('.env'):
            print("   📄 .env file exists")
            with open('.env', 'r') as f:
                lines = f.readlines()
            
            print(f"   📊 File has {len(lines)} lines")
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line.startswith('NB_PA_TOKEN=') and not line.startswith('NB_PA_TOKEN_REFRESH='):
                    token_preview = line[12:32] + '...' if len(line) > 32 else line[12:]
                    print(f"   Line {i}: NB_PA_TOKEN={token_preview} (length: {len(line)-12})")
                elif line.startswith('NB_PA_TOKEN_REFRESH='):
                    token_preview = line[20:30] + '...' if len(line) > 30 else line[20:]
                    print(f"   Line {i}: NB_PA_TOKEN_REFRESH={token_preview} (length: {len(line)-20})")
                elif line.startswith('NB_'):
                    print(f"   Line {i}: {line}")
        else:
            print("   ❌ .env file not found!")
            
    except Exception as e:
        print(f"   ❌ Error reading .env file: {e}")

if __name__ == "__main__":
    debug_token_loading()