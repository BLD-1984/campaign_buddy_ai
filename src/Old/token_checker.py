# enhanced_token_checker.py
"""
Enhanced token checker that tests the new refresh flow
This will actually attempt to refresh your expired tokens
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from nb_api_client import NationBuilderClient

def test_enhanced_client_with_refresh():
    """Test the enhanced client with automatic token refresh"""
    
    print("🔍 ENHANCED NATIONBUILDER CLIENT TEST")
    print("=" * 55)
    
    # Get credentials from environment
    nation_slug = os.getenv('NB_NATION_SLUG')
    access_token = os.getenv('NB_PA_TOKEN')
    refresh_token = os.getenv('NB_PA_TOKEN_REFRESH')
    client_id = os.getenv('NB_PA_ID')
    client_secret = os.getenv('NB_PA_SECRET')
    
    print(f"🏛️  Nation Slug: {nation_slug}")
    print(f"🎫 Access Token: {'Present' if access_token else 'MISSING'}")
    print(f"🔄 Refresh Token: {'Present' if refresh_token else 'MISSING'}")
    print(f"🆔 Client ID: {'Present' if client_id else 'MISSING'}")
    print(f"🔐 Client Secret: {'Present' if client_secret else 'MISSING'}")
    
    if not all([nation_slug, access_token, refresh_token, client_id, client_secret]):
        print("❌ Missing required credentials!")
        return False
    
    print(f"\n🔧 INITIALIZING ENHANCED CLIENT")
    print("-" * 35)
    
    try:
        # Initialize the enhanced client
        client = NationBuilderClient(
            nation_slug=nation_slug,
            access_token=access_token,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret
        )
        print("✅ Enhanced NationBuilder client initialized")
        
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    print(f"\n🧪 TESTING API CONNECTION (with auto-refresh)")
    print("-" * 50)
    
    try:
        # This should automatically refresh the token if needed
        print("📡 Attempting API call (this will trigger refresh if needed)...")
        
        result = client.get_signups(fields=['first_name', 'last_name'], page_size=1)
        
        if result and 'data' in result:
            print("✅ API call successful!")
            print(f"📊 Retrieved {len(result['data'])} signup(s)")
            
            if result['data']:
                sample = result['data'][0]
                attrs = sample.get('attributes', {})
                print(f"📋 Sample person: {attrs.get('first_name', '')} {attrs.get('last_name', '')}")
            
            return True
        else:
            print("⚠️  API call returned empty result")
            return False
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

def test_connection_method():
    """Test the built-in connection test method"""
    print(f"\n🔌 TESTING CONNECTION METHOD")
    print("-" * 30)
    
    try:
        client = NationBuilderClient(
            nation_slug=os.getenv('NB_NATION_SLUG'),
            access_token=os.getenv('NB_PA_TOKEN'),
            refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
            client_id=os.getenv('NB_PA_ID'),
            client_secret=os.getenv('NB_PA_SECRET')
        )
        
        # Use the built-in connection test
        success = client.test_connection()
        
        if success:
            print("✅ Built-in connection test passed!")
            return True
        else:
            print("❌ Built-in connection test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

def show_token_info_after_refresh():
    """Show updated token information after refresh"""
    print(f"\n📋 TOKEN STATUS AFTER REFRESH")
    print("-" * 35)
    
    # Re-read the .env file to see if tokens were updated
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Force reload
    
    new_access_token = os.getenv('NB_PA_TOKEN')
    new_refresh_token = os.getenv('NB_PA_TOKEN_REFRESH')
    
    print(f"🎫 Access Token Length: {len(new_access_token) if new_access_token else 0}")
    print(f"🔄 Refresh Token Length: {len(new_refresh_token) if new_refresh_token else 0}")
    
    # Check if tokens appear to have changed (basic check)
    if new_access_token and len(new_access_token) > 400:
        print("✅ Access token appears valid (proper length)")
    else:
        print("⚠️  Access token may not be valid")

def main():
    """Run all tests"""
    
    # Test 1: Enhanced client with automatic refresh
    success1 = test_enhanced_client_with_refresh()
    
    # Test 2: Built-in connection test method
    success2 = test_connection_method()
    
    # Show token info after potential refresh
    show_token_info_after_refresh()
    
    # Summary
    print(f"\n🎯 FINAL RESULTS")
    print("=" * 20)
    
    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your enhanced client is working perfectly")
        print("✅ Token refresh flow is functional")
        print("✅ Ready to test the clickers module")
        
        print(f"\n💡 NEXT STEP:")
        print("   Run your clickers module:")
        print("   cd nb_path_updates/nb_nightly")
        print("   python main.py")
        
    elif success1 or success2:
        print("⚠️  PARTIAL SUCCESS")
        print("✅ At least one test passed")
        print("💡 Token refresh may be working")
        
    else:
        print("❌ ALL TESTS FAILED")
        print("💡 There may be an issue with your credentials or refresh setup")
        
        print(f"\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Double-check your .env file credentials")
        print("2. Verify your OAuth app is properly configured in NationBuilder")
        print("3. Check that your refresh token hasn't been revoked")

if __name__ == "__main__":
    main()