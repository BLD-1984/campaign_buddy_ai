# oauth_token_exchanger.py
"""
OAuth Token Exchange Script
Exchanges authorization code for fresh access and refresh tokens
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def exchange_code_for_tokens():
    """
    Exchange authorization code for access and refresh tokens
    """
    print("🔐 OAUTH TOKEN EXCHANGE")
    print("=" * 30)
    
    # Get credentials from environment
    nation_slug = os.getenv('NB_NATION_SLUG')
    client_id = os.getenv('NB_PA_ID')
    client_secret = os.getenv('NB_PA_SECRET')
    
    print(f"🏛️  Nation: {nation_slug}")
    print(f"🆔 Client ID: {client_id[:10]}..." if client_id else "❌ Missing Client ID")
    print(f"🔐 Client Secret: {'Present' if client_secret else '❌ Missing'}")
    
    if not all([nation_slug, client_id, client_secret]):
        print("\n❌ Missing required credentials in .env file!")
        return
    
    # Get the callback URL (you'll need to tell us what this is)
    print(f"\n📋 STEP 1: What's your OAuth callback URL?")
    print("   (Check Settings > Developer > Your apps in NationBuilder)")
    print("   Common options:")
    print("   - http://localhost:8000/callback")  
    print("   - http://localhost:3000/callback")
    print("   - https://yourapp.com/callback")
    
    callback_url = input("\n🔗 Enter your callback URL: ").strip()
    
    if not callback_url:
        print("❌ Callback URL is required!")
        return
    
    # Build authorization URL
    auth_url = (
        f"https://{nation_slug}.nationbuilder.com/oauth/authorize?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={callback_url}"
    )
    
    print(f"\n📋 STEP 2: Visit this URL in your browser:")
    print("=" * 50)
    print(auth_url)
    print("=" * 50)
    print("\n📝 Instructions:")
    print("   1. Copy the URL above")
    print("   2. Paste it in your browser")
    print("   3. Log in and approve the app")
    print("   4. You'll be redirected to a URL like:")
    print(f"      {callback_url}?code=SOME_LONG_CODE")
    print("   5. Copy the code from the URL (after 'code=')")
    print("   6. The page might show an error - that's normal!")
    
    auth_code = input(f"\n🎫 Enter the authorization code: ").strip()
    
    if not auth_code:
        print("❌ Authorization code is required!")
        return
    
    print(f"\n🔄 Exchanging code for tokens...")
    
    # Exchange code for tokens
    token_url = f"https://{nation_slug}.nationbuilder.com/oauth/token"
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': callback_url,
        'code': auth_code
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.post(token_url, data=token_data, headers=headers)
        
        if response.status_code == 200:
            tokens = response.json()
            
            print("✅ SUCCESS! Got fresh tokens:")
            print(f"   🎫 Access Token: {tokens['access_token']}")
            print(f"   🔄 Refresh Token: {tokens['refresh_token']}")
            print(f"   ⏰ Expires in: {tokens['expires_in']} seconds ({tokens['expires_in']/3600:.1f} hours)")
            
            # Update .env file
            update_env_file(tokens['access_token'], tokens['refresh_token'])
            
            # Test the new tokens
            test_new_tokens(tokens['access_token'])
            
        else:
            print(f"❌ Token exchange failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            
            if "invalid_grant" in response.text:
                print("\n💡 The authorization code may have:")
                print("   - Expired (codes expire in 10 minutes)")
                print("   - Been used already (codes are single-use)")
                print("   - Been copied incorrectly")
                print("\n🔄 Try going through the authorization URL again")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

def update_env_file(access_token: str, refresh_token: str):
    """Update .env file with new tokens"""
    print(f"\n📁 Updating .env file with new tokens...")
    
    try:
        # Read current .env file
        env_lines = []
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_lines = f.readlines()
        
        # Update token lines
        updated_lines = []
        access_token_updated = False
        refresh_token_updated = False
        
        for line in env_lines:
            if line.startswith('NB_PA_TOKEN=') and not line.startswith('NB_PA_TOKEN_REFRESH='):
                updated_lines.append(f'NB_PA_TOKEN={access_token}\n')
                access_token_updated = True
            elif line.startswith('NB_PA_TOKEN_REFRESH='):
                updated_lines.append(f'NB_PA_TOKEN_REFRESH={refresh_token}\n')
                refresh_token_updated = True
            else:
                updated_lines.append(line)
        
        # Add tokens if they weren't found
        if not access_token_updated:
            updated_lines.append(f'NB_PA_TOKEN={access_token}\n')
        if not refresh_token_updated:
            updated_lines.append(f'NB_PA_TOKEN_REFRESH={refresh_token}\n')
        
        # Write updated .env file
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
            
        print("✅ .env file updated successfully!")
        
    except Exception as e:
        print(f"❌ Failed to update .env file: {e}")

def test_new_tokens(access_token: str):
    """Test the new tokens with a simple API call"""
    print(f"\n🧪 Testing new tokens...")
    
    nation_slug = os.getenv('NB_NATION_SLUG')
    test_url = f"https://{nation_slug}.nationbuilder.com/api/v2/signups"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    params = {'page[size]': 1}
    
    try:
        response = requests.get(test_url, headers=headers, params=params)
        
        if response.status_code == 200:
            print("✅ Token test successful!")
            data = response.json()
            if data.get('data'):
                print(f"📊 API is working - retrieved {len(data['data'])} signup(s)")
            print("\n🎉 You're all set! Your tokens are working.")
            print("\n💡 NEXT STEPS:")
            print("   1. Run: python enhanced_token_checker.py")
            print("   2. Run: cd nb_path_updates/nb_nightly && python main.py")
            
        else:
            print(f"❌ Token test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Token test error: {e}")

if __name__ == "__main__":
    exchange_code_for_tokens()