import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BREVO_API_KEY")
print("BREVO_API_KEY:", api_key)

url = "https://api.brevo.com/v3/smtp/email"
headers = {
    "accept": "application/json",
    "api-key": api_key,
    "content-type": "application/json"
}
payload = {
    "sender": {"name": "INS Statistical Portal", "email": "no-reply@ins.tn"},
    "to": [{"email": "contact@ins.tn"}],
    "subject": "Test Brevo from Python",
    "htmlContent": "<h1>This is a test OTP verification mail!</h1>"
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print("Status code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("Error occurred:", e)
