# explore_actual_tags.py
"""
Explore the actual tag names in your NationBuilder system
to understand what 'Met at...' tags exist
"""

import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.append('src')
from nb_api_client import NationBuilderClient
import os
import csv
from datetime import datetime


def load_client():
    return NationBuilderClient(
        nation_slug=os.getenv('NB_NATION_SLUG'),
        access_token=os.getenv('NB_PA_TOKEN'),
        refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
        client_id=os.getenv('NB_PA_ID'),
        client_secret=os.getenv('NB_PA_SECRET')
    )


def get_all_tags(client):
    """Get all tags from your nation"""
    print("🏷️  Getting ALL tags from your nation")
    print("-" * 50)
    
    all_tags = []
    page = 1
    
    try:
        while True:
            result = client.get_signup_tags(page_size=100)
            tags = result.get('data', [])
            
            if not tags:
                break
                
            all_tags.extend(tags)
            print(f"   Page {page}: Found {len(tags)} tags (Total: {len(all_tags)})")
            
            # Check if we need more pages
            if len(tags) < 100:
                break
            page += 1
            
            # Remove artificial safety limit - let it run until it finds all tags
            if page % 25 == 0:  # Just a progress indicator every 25 pages
                print(f"   🔄 Still going... (Page {page}, Total: {len(all_tags)} tags)")
                # Optional: Ask user if they want to continue for very large datasets
                if page > 100:
                    print(f"   ⚠️  This is a lot of tags ({len(all_tags)})! The 'Met at' tags should be found soon...")
                    if page > 200:
                        print(f"   🛑 Stopping at 200 pages (20,000 tags) to avoid infinite loop")
                        break
        
        print(f"✅ Total tags found: {len(all_tags)}")
        return all_tags
        
    except Exception as e:
        print(f"❌ Error getting tags: {e}")
        return []


def analyze_tags(tags):
    """Analyze tags to find patterns and 'Met at' variations"""
    print(f"\n🔍 Analyzing {len(tags)} tags")
    print("-" * 50)
    
    # Look for different variations of "met at"
    met_variations = []
    met_keywords = ['met at', 'met_at', 'metat', 'meet at', 'meet_at']
    july_keywords = ['2025-07', '2025_07', 'july', 'july 2025', '07-2025', '07_2025']
    deployment_keywords = ['deployment', 'event', 'rally', 'online', 'other']
    
    tag_analysis = {
        'total': len(tags),
        'met_at_exact': [],
        'met_at_similar': [],
        'july_2025_tags': [],
        'deployment_related': [],
        'sample_tags': []
    }
    
    for tag in tags:
        tag_name = tag.get('attributes', {}).get('name', '').lower()
        tag_id = tag.get('id')
        original_name = tag.get('attributes', {}).get('name', '')
        
        # Store first 20 tags as samples
        if len(tag_analysis['sample_tags']) < 20:
            tag_analysis['sample_tags'].append(original_name)
        
        # Check for exact "met at" patterns
        if any(keyword in tag_name for keyword in met_keywords):
            tag_analysis['met_at_similar'].append({
                'id': tag_id,
                'name': original_name
            })
            
            # Check if it's exactly what we're looking for
            if tag_name.startswith('met at') and any(july_kw in tag_name for july_kw in july_keywords):
                tag_analysis['met_at_exact'].append({
                    'id': tag_id, 
                    'name': original_name
                })
        
        # Check for July 2025 tags
        if any(july_kw in tag_name for july_kw in july_keywords):
            tag_analysis['july_2025_tags'].append({
                'id': tag_id,
                'name': original_name
            })
        
        # Check for deployment-related tags
        if any(deploy_kw in tag_name for deploy_kw in deployment_keywords):
            tag_analysis['deployment_related'].append({
                'id': tag_id,
                'name': original_name
            })
    
    return tag_analysis


def print_analysis_results(analysis):
    """Print the analysis results"""
    print(f"\n📊 TAG ANALYSIS RESULTS")
    print("=" * 50)
    
    print(f"Total tags: {analysis['total']}")
    print(f"Exact 'Met at' matches: {len(analysis['met_at_exact'])}")
    print(f"Similar 'Met at' tags: {len(analysis['met_at_similar'])}")
    print(f"July 2025 tags: {len(analysis['july_2025_tags'])}")
    print(f"Deployment-related tags: {len(analysis['deployment_related'])}")
    
    # Show exact matches
    if analysis['met_at_exact']:
        print(f"\n🎯 EXACT 'Met at' MATCHES:")
        for tag in analysis['met_at_exact']:
            print(f"   ID {tag['id']}: '{tag['name']}'")
    
    # Show similar matches
    if analysis['met_at_similar']:
        print(f"\n🔍 SIMILAR 'Met at' TAGS:")
        for tag in analysis['met_at_similar'][:10]:  # First 10
            print(f"   ID {tag['id']}: '{tag['name']}'")
        if len(analysis['met_at_similar']) > 10:
            print(f"   ... and {len(analysis['met_at_similar']) - 10} more")
    
    # Show July 2025 tags
    if analysis['july_2025_tags']:
        print(f"\n📅 JULY 2025 TAGS:")
        for tag in analysis['july_2025_tags'][:10]:  # First 10
            print(f"   ID {tag['id']}: '{tag['name']}'")
        if len(analysis['july_2025_tags']) > 10:
            print(f"   ... and {len(analysis['july_2025_tags']) - 10} more")
    
    # Show deployment-related tags  
    if analysis['deployment_related']:
        print(f"\n🚀 DEPLOYMENT-RELATED TAGS:")
        for tag in analysis['deployment_related'][:10]:  # First 10
            print(f"   ID {tag['id']}: '{tag['name']}'")
        if len(analysis['deployment_related']) > 10:
            print(f"   ... and {len(analysis['deployment_related']) - 10} more")
    
    # Show sample of all tags
    print(f"\n📋 SAMPLE OF ALL TAGS (first 20):")
    for i, tag_name in enumerate(analysis['sample_tags'], 1):
        print(f"   {i:2d}. {tag_name}")


def export_all_tags_to_csv(tags):
    """Export all tags to CSV for manual review"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"all_tags_{timestamp}.csv"
    
    print(f"\n📄 Exporting all tags to CSV: {filename}")
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Tag ID', 'Tag Name', 'Taggings Count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for tag in tags:
                attrs = tag.get('attributes', {})
                writer.writerow({
                    'Tag ID': tag.get('id', ''),
                    'Tag Name': attrs.get('name', ''),
                    'Taggings Count': attrs.get('taggings_count', 0)
                })
        
        print(f"✅ Exported {len(tags)} tags to {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error exporting tags: {e}")
        return None


def main():
    print("🔍 Exploring Actual Tag Names in Your Nation")
    print("=" * 60)
    
    client = load_client()
    
    # Get all tags
    all_tags = get_all_tags(client)
    
    if not all_tags:
        print("❌ No tags found. Cannot analyze.")
        return
    
    # Analyze the tags
    analysis = analyze_tags(all_tags)
    
    # Print results
    print_analysis_results(analysis)
    
    # Export to CSV for manual review
    csv_file = export_all_tags_to_csv(all_tags)
    
    print(f"\n" + "=" * 60)
    print("🎯 CONCLUSIONS:")
    
    if analysis['met_at_exact']:
        print("✅ Found exact 'Met at' tags matching your filter!")
        print("   → The complex filter should work with these tags")
    elif analysis['met_at_similar']:
        print("⚠️  Found similar 'Met at' tags, but not exact matches")
        print("   → You may need to adjust the filter patterns")
    elif analysis['july_2025_tags'] or analysis['deployment_related']:
        print("🔍 Found related tags that might be what you're looking for")
        print("   → Check the CSV file to see the exact tag names")
    else:
        print("❌ No 'Met at' or related tags found")
        print("   → The tags may not exist yet, or have different names")
    
    if csv_file:
        print(f"\n📁 Review the CSV file '{csv_file}' to see all tag names")
        print("🔍 Look for the exact tags you want to filter by")
        print("📝 Then we can update the filter patterns accordingly")


if __name__ == "__main__":
    main()