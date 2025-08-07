# nb_path_updates/endpoint_explorer.py
"""
Explore NationBuilder API v2 endpoints to find email-related resources
Run this to discover what email endpoints are actually available
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
load_dotenv()

from src.nb_api_client import NationBuilderClient
import json


def explore_endpoints(client: NationBuilderClient):
    """Explore various email-related endpoint possibilities"""
    
    print("🔍 Exploring NationBuilder API v2 Email-Related Endpoints")
    print("=" * 60)
    
    # List of possible email-related endpoints to try
    email_endpoints = [
        'blasts',
        'email_blasts', 
        'emails',
        'broadcasts',
        'email_broadcasts',
        'email_recipients',
        'recipients',
        'email_deliveries',
        'deliveries',
        'email_clicks',
        'clicks',
        'email_opens',
        'opens',
        'email_interactions',
        'interactions',
        'email_stats',
        'stats',
        'email_campaigns',
        'campaigns',
        'mailings',
        'email_mailings',
        'communications',
        'email_communications',
        'messages',
        'email_messages'
    ]
    
    found_endpoints = []
    
    for endpoint in email_endpoints:
        print(f"\n📡 Testing endpoint: /api/v2/{endpoint}")
        
        try:
            # Try basic GET request with small page size
            response = client.session.get(f"{client.base_url}/{endpoint}", params={'page[size]': 1})
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ SUCCESS! Found working endpoint")
                    
                    # Show structure
                    if 'data' in data:
                        data_items = data['data']
                        print(f"   📊 Data items: {len(data_items)}")
                        
                        if data_items and len(data_items) > 0:
                            first_item = data_items[0]
                            print(f"   📋 Sample item type: {first_item.get('type', 'unknown')}")
                            
                            # Show available attributes
                            if 'attributes' in first_item:
                                attrs = list(first_item['attributes'].keys())[:10]  # First 10 attributes
                                print(f"   🏷️  Sample attributes: {', '.join(attrs)}")
                            
                            # Show the first item structure (pretty printed)
                            print(f"   📄 Sample item structure:")
                            print(json.dumps(first_item, indent=6)[:500] + "...")
                    
                    found_endpoints.append(endpoint)
                    
                except Exception as e:
                    print(f"   ⚠️  Valid response but JSON parse error: {e}")
                    
            elif response.status_code == 404:
                print(f"   ❌ Not found")
            elif response.status_code == 401:
                print(f"   🔒 Unauthorized (check token)")
            elif response.status_code == 403:
                print(f"   🚫 Forbidden (insufficient permissions)")
            else:
                print(f"   ⚠️  Other error: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY OF WORKING EMAIL ENDPOINTS")
    print("=" * 60)
    
    if found_endpoints:
        for endpoint in found_endpoints:
            print(f"✅ /api/v2/{endpoint}")
    else:
        print("❌ No email-related endpoints found")
        print("\n💡 Suggestions:")
        print("   1. Check your API token permissions")
        print("   2. Your NationBuilder instance might not have email blast data")
        print("   3. Email data might be under different endpoint names")
        print("   4. Try looking at the interactive API docs in your NB control panel")
    
    return found_endpoints


def explore_contacts_endpoint(client: NationBuilderClient):
    """Explore the contacts endpoint which might have email blast data"""
    
    print("\n🔍 Exploring Contacts Endpoint (might have email blast data)")
    print("=" * 60)
    
    try:
        # Try contacts endpoint
        response = client.session.get(f"{client.base_url}/contacts", params={'page[size]': 5})
        
        print(f"📡 Testing /api/v2/contacts")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS! Found contacts endpoint")
            
            if 'data' in data and data['data']:
                for i, contact in enumerate(data['data'][:3]):  # Show first 3 contacts
                    attrs = contact.get('attributes', {})
                    method = attrs.get('method', 'unknown')
                    created_at = attrs.get('created_at', 'unknown')
                    
                    print(f"   📋 Contact {i+1}: method={method}, created={created_at}")
                    
                    # Look specifically for email_blast method
                    if method == 'email_blast':
                        print(f"      🎯 FOUND EMAIL BLAST CONTACT!")
                        print(json.dumps(contact, indent=8)[:300] + "...")
                        
                        # Check for click/engagement data
                        status = attrs.get('status', '')
                        broadcaster_id = attrs.get('broadcaster_id', '')
                        note = attrs.get('note', '')
                        
                        print(f"      📊 Status: {status}")
                        print(f"      📢 Broadcaster ID: {broadcaster_id}")
                        print(f"      📝 Note: {note}")
            
            return True
            
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   💥 Request failed: {e}")
        return False


def main():
    """Main exploration function"""
    
    try:
        # Initialize client
        client = NationBuilderClient(
            nation_slug=os.getenv('NB_NATION_SLUG'),
            access_token=os.getenv('NB_PA_TOKEN'),
            refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
            client_id=os.getenv('NB_PA_ID'),
            client_secret=os.getenv('NB_PA_SECRET')
        )
        
        print("✅ NationBuilder client initialized")
        
        # Explore email endpoints
        found_endpoints = explore_endpoints(client)
        
        # Explore contacts endpoint (might have email blast data)
        explore_contacts_endpoint(client)
        
        print("\n" + "=" * 60)
        print("🎯 RECOMMENDATIONS FOR CLICKERS FILTER")
        print("=" * 60)
        
        if 'contacts' in found_endpoints or found_endpoints:
            print("✅ Found some working endpoints!")
            print("   💡 Next steps:")
            print("   1. Update clickers.py to use working endpoints")
            print("   2. Look for contacts with method='email_blast'")
            print("   3. Filter by date and look for click indicators")
        else:
            print("❌ No email endpoints found")
            print("   💡 Alternative approaches:")
            print("   1. Use contacts endpoint to find email_blast communications")
            print("   2. Look for tags that indicate email engagement")
            print("   3. Use signup activity/interaction data")
            print("   4. Check if your NB instance has email blast history")
        
        print("\n📚 Additional Resources:")
        print(f"   🌐 Interactive API docs: https://{client.nation_slug}.nationbuilder.com/api/v2/docs")
        print("   📖 Check your NB control panel under Settings > Developer > API testing")
        
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        print("   💡 Check your .env file has the correct credentials")


if __name__ == "__main__":
    main()