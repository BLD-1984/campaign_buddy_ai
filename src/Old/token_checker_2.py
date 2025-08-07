import os
from dotenv import load_dotenv
from src.nb_api_client import NationBuilderClient

load_dotenv()

client = NationBuilderClient(
    nation_slug=os.getenv('NB_NATION_SLUG'),
    access_token=os.getenv('NB_PA_TOKEN'),
    refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
    client_id=os.getenv('NB_PA_ID'),
    client_secret=os.getenv('NB_PA_SECRET')
)

try:
    # This will trigger refresh if needed
    result = client.get_signups(page_size=1)
    print("✅ Token refresh flow works! API responded:", result)
except Exception as e:
    print("❌ Token refresh failed:", e)
    