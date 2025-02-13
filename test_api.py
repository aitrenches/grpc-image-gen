
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_URL = "http://127.0.0.1:5000/generate"  # Adjust if hosted elsewhere
API_KEY = os.getenv("API_SECRET_KEY")  # Use the correct API key

headers = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY
}

payload = {
    "prompt": "A futuristic city skyline at sunset",
    "size": "1024x1024"
}

response = requests.post(API_URL, json=payload, headers=headers)

print("Status Code:", response.status_code)
print("Response:", response.json())
