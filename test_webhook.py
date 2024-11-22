import httpx
import json

webhook_url = "http://127.0.0.1:8000/payments/webhook/"

payload = {"event": "charge.success", "data": {"amount": 1000, "currency": "USD"}}

headers = {"Content-Type": "application/json"}
payload_json = json.dumps(payload)

with httpx.Client() as client:
    response = client.post(webhook_url, data=payload_json, headers=headers)

print(response.status_code)
print(response.json())
