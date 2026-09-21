import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

# Use the token we got
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmZDU0YWE2OC00OTVhLTQyMjktYmIxZi0wZTI2ODI3ZjYyM2YiLCJ0eXBlIjoiYWNjZXNzIiwiaWF0IjoxNzg4MjIzOTUyLCJleHAiOjE3ODgyMjc1NTJ9.TMLsCrfNnYMk9rL0uees2baqbD11zyU7BJ7N7KymF2Q"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

print("=" * 60)
print("Testing QR Code Generation Flow")
print("=" * 60)

# 1. Create product
print("\n1. Creating product...")
r = requests.post(f'{BASE_URL}/products', headers=headers, json={
    "sku": "TEST-QR-001",
    "product_name": "Test QR Product",
    "category_id": "b3e850c6-934e-47aa-899d-e44c0b269412",
    "selling_price": "99.99",
    "currency": "USD"
})
print(f"   Status: {r.status_code}")
prod = r.json()['data']
product_id = prod['id']
print(f"   Product ID: {product_id}")

# 2. Create QR channel
print("\n2. Creating QR Code channel...")
r = requests.post(f'{BASE_URL}/outputs/channels', headers=headers, json={
    "name": "QR Test Channel",
    "output_type": "qr_code",
    "status": "active",
    "configuration": {"box_size": 8, "border": 2, "error_correction": "M"}
})
print(f"   Status: {r.status_code}")
chan = r.json()['data']
channel_id = chan['id']
print(f"   Channel ID: {channel_id}")

# 3. Create output job
print("\n3. Creating output job...")
r = requests.post(f'{BASE_URL}/outputs/jobs', headers=headers, json={
    "output_channel_id": channel_id,
    "product_id": product_id
})
print(f"   Status: {r.status_code}")
job = r.json()['data']
job_id = job['id']
print(f"   Job ID: {job_id}")
print(f"   Initial Status: {job['status']}")

# 4. Wait for worker to process
print("\n4. Waiting for Celery worker to process job...")
for i in range(10):
    time.sleep(2)
    r = requests.get(f'{BASE_URL}/outputs/jobs/{job_id}', headers=headers)
    result = r.json()['data']
    print(f"   Check {i+1}: Status = {result['status']}")
    if result['status'] in ('completed', 'failed'):
        break

# 5. Check final result
print("\n5. Final result:")
r = requests.get(f'{BASE_URL}/outputs/jobs/{job_id}', headers=headers)
result = r.json()['data']
print(f"   Status: {result['status']}")
print(f"   Attempts: {result['attempts']}")
if result.get('last_error'):
    print(f"   Error: {result['last_error']}")
if result.get('payload'):
    print(f"   Payload keys: {list(result['payload'].keys())}")
    if 'qr_image_base64' in result['payload']:
        print(f"   ✅ QR CODE GENERATED! Length: {len(result['payload']['qr_image_base64'])} chars")
        print(f"   Target URL: {result['payload'].get('target_url')}")
    else:
        print(f"   No QR in payload: {json.dumps(result['payload'], indent=2)[:500]}")
else:
    print("   No payload")

# 6. Test public price endpoint
print("\n6. Testing public price endpoint...")
r = requests.get(f'{BASE_URL}/public/price/{product_id}')
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()['data']
    print(f"   Product: {data['product_name']}")
    print(f"   Price: {data['currency']} {data['price']}")

print("\n" + "=" * 60)
print("Test complete")
print("=" * 60)