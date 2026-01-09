import requests

import os
from dotenv import load_dotenv

api_key = os.getenv("PERPLEXITY_API_KEY")
url = "https://api.perplexity.ai/chat/completions"
payload = {
    "model": "llama-3.1-70b-instruct",
    "messages": [{"role": "user", "content": "1 факт про космос для детей"}]
}
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

resp = requests.post(url, json=payload, headers=headers)
print(f"Status: {resp.status_code}")
print(resp.json())