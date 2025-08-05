import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

NATION = "larouchepac"
TOKEN_URL = f"https://{NATION}.nationbuilder.com/oauth/token"

if len(sys.argv) != 2:
    print("Usage: python nationbuilder_token_exchange.py <AUTH_CODE>")
    sys.exit(1)

auth_code = sys.argv[1]

data = {
    "client_id": os.getenv("NB_PA_ID"),
    "client_secret": os.getenv("NB_PA_SECRET"),
    "redirect_uri": os.getenv("NB_PA_REDIRECT_URI"),
    "code": auth_code,
    "grant_type": "authorization_code"
}

try:
    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    print("Access token response:")
    print(response.json())
except requests.RequestException as e:
    print("Error exchanging code for token:", e)
    if response is not None:
        print("Response:", response.text)
