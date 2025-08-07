# simple_token_refresh.py
"""
Simple test to refresh tokens using current credentials
"""

import os
import requests
from dotenv import load_dotenv

def test_token_refresh():
    """Test token refresh with current credentials"""
    
    print("🔄 SIMPLE TOKEN REFRESH TEST")
    print("=" * 35)
    
    load_dotenv()
    
    nation_slug = os.getenv('NB_NATION_SLUG')
    refresh_token = os.getenv('NB_PA_TOKEN_REFRESH')
    client_id = os.getenv('NB_PA_ID')
    client_secret = os.getenv('NB_PA_SECRET')
    
    print(f"🏛️  Nation: {nation_slug}")
    print(f"🔄 Refresh Token: {refresh_token[:10]}... (length: {len(refresh_token)})")
    print(f"🆔 Client ID: {client_id[:10]}...")
    print(f"🔐 Client Secret: {'Present' if client_secret else 'Missing'}")
    
    if not all([nation_slug, refresh_token, client_id, client_secret]):
        print("❌ Missing required credentials")
        return
    
    print(f"\n🔄 Attempting token refresh...")
    
    # Refresh token request
    refresh_url = f"https://{nation_slug}.nationbuilder.com/oauth/token"
    refresh_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.post(refresh_url, data=refresh_data, headers=headers)
        
        print(f"📡 Refresh Response:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            tokens = response.json()
            print("✅ REFRESH SUCCESSFUL!")
            print(f"   🎫 New Access Token: {tokens['access_token'][:20]}...")
            print(f"   🔄 New Refresh Token: {tokens['refresh_token'][:20]}...")
            print(f"   ⏰ Expires in: {tokens['expires_in']} seconds")
            
            # Test the new access token immediately
            test_new_token_immediately(tokens['access_token'], nation_slug)
            
            # Offer to update .env file
            update_choice = input("\n💾 Update .env file with new tokens? (y/n): ").lower()
            if update_choice == 'y':
                update_env_with_tokens(tokens['access_token'], tokens['refresh_token'])
                
        else:
            print("❌ REFRESH FAILED!")
            try:
                error = response.json()
                print(f"   Error: {error}")
                
                if error.get('error') == 'invalid_grant':
                    print("\n💡 The refresh token is invalid. This means:")
                    print("   - The refresh token has expired or been revoked")
                    print("   - You need to go through the full OAuth flow again")
                    print("   - Run: python oauth_token_exchanger.py")
                    
            except:
                print(f"   Raw response: {response.text}")
                
    except Exception as e:
        print(f"💥 Request failed: {e}")

def test_new_token_immediately(access_token: str, nation_slug: str):
    """Test the new access token immediately"""
    print(f"\n🧪 Testing new token immediately...")
    
    test_url = f"https://{nation_slug}.nationbuilder.com/api/v2/signups"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    params = {'page[size]': 1}
    
    try:
        response = requests.get(test_url, headers=headers, params=params)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ NEW TOKEN WORKS!")
            data = response.json()
            if data.get('data'):
                print(f"   📊 Retrieved {len(data['data'])} signup(s)")
                
                # Show sample data
                if data['data']:
                    sample = data['data'][0]
                    attrs = sample.get('attributes', {})
                    name = f"{attrs.get('first_name', '')} {attrs.get('last_name', '')}".strip()
                    print(f"   👤 Sample person: {name or 'No name'}")
        else:
            print("   ❌ NEW TOKEN FAILED!")
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Response: {response.text[:200]}")
                
    except Exception as e:
        print(f"   💥 Test failed: {e}")

def update_env_with_tokens(access_token: str, refresh_token: str):
    """Update .env file with working tokens"""
    print(f"\n📁 Updating .env file...")
    
    try:
        # Read current .env
        env_lines = []
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_lines = f.readlines()
        
        # Update lines
        updated_lines = []
        access_updated = False
        refresh_updated = False
        
        for line in env_lines:
            if line.startswith('NB_PA_TOKEN=') and not line.startswith('NB_PA_TOKEN_REFRESH='):
                updated_lines.append(f'NB_PA_TOKEN={access_token}\n')
                access_updated = True
                print(f"   ✅ Updated access token")
            elif line.startswith('NB_PA_TOKEN_REFRESH='):
                updated_lines.append(f'NB_PA_TOKEN_REFRESH={refresh_token}\n')
                refresh_updated = True
                print(f"   ✅ Updated refresh token")
            else:
                updated_lines.append(line)
        
        # Add if missing
        if not access_updated:
            updated_lines.append(f'NB_PA_TOKEN={access_token}\n')
            print(f"   ✅ Added access token")
        if not refresh_updated:
            updated_lines.append(f'NB_PA_TOKEN_REFRESH={refresh_token}\n')
            print(f"   ✅ Added refresh token")
        
        # Write file
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ .env file updated successfully!")
        
        # Reload and verify
        print(f"\n🔄 Reloading .env to verify...")
        load_dotenv(override=True)
        
        new_access = os.getenv('NB_PA_TOKEN')
        new_refresh = os.getenv('NB_PA_TOKEN_REFRESH')
        
        if new_access == access_token and new_refresh == refresh_token:
            print("✅ Verification successful - tokens loaded correctly!")
        else:
            print("❌ Verification failed - tokens don't match")
            
    except Exception as e:
        print(f"❌ Failed to update .env: {e}")

if __name__ == "__main__":
    test_token_refresh()