import requests
import json
import time
import base64

BASE_URL = "http://localhost:8000/api/v1"

# Register fresh user
r = requests.post(f'{BASE_URL}/auth/register', json={
    'email': 'qrtest@test.com',
    'first_name': 'QR',
    'last_name': 'Tester',
    'password': 'testpass123',
    'confirm_password': 'testpass123',
    'organization_name': 'QR Test Org'
})
print("Register:", r.status_code)
if r.status_code == 201:
    token = r.json()['data']['access_token']
elif r.status_code == 409:
    r = requests.post(f'{BASE_URL}/auth/login', json={'email': 'qrtest@test.com', 'password': 'testpass123'})
    print("Login:", r.status_code)
    token = r.json()['data']['access_token']
else:
    print(r.json())
    exit(1)

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print("Auth OK")

# Get first product
r = requests.get(f'{BASE_URL}/products?page=1&page_size=1', headers=headers)
products = r.json()['data']
product = products[0]
print(f"\nProduct: {product['product_name']} ({product['id']})")

# Create QR channel
r = requests.post(f'{BASE_URL}/outputs/channels', headers=headers, json={
    "name": "QR Price Tag",
    "output_type": "qr_code",
    "status": "active",
    "configuration": {"box_size": 10, "border": 2, "error_correction": "M"}
})
print(f"Channel: {r.status_code}")
if r.status_code == 201:
    channel_id = r.json()['data']['id']
else:
    print(r.json())
    r = requests.get(f'{BASE_URL}/outputs/channels?page=1&page_size=20', headers=headers)
    qr_channels = [c for c in r.json()['data'] if c['output_type'] == 'qr_code']
    channel_id = qr_channels[0]['id'] if qr_channels else None
print(f"Channel ID: {channel_id}")

# Create output job
print("\nCreating QR output job...")
r = requests.post(f'{BASE_URL}/outputs/jobs', headers=headers, json={
    "output_channel_id": channel_id,
    "product_id": product['id'],
})
print(f"  Status: {r.status_code}")
if r.status_code != 201:
    print(f"  Error: {r.json()}")
    exit(1)
job_id = r.json()['data']['id']
print(f"  Job: {job_id}")

# Wait for worker
print("\nWaiting for Celery worker...")
for i in range(15):
    time.sleep(2)
    r = requests.get(f'{BASE_URL}/outputs/jobs/{job_id}', headers=headers)
    result = r.json()['data']
    print(f"  Check {i+1}: {result['status']}")
    if result['status'] in ('completed', 'failed'):
        break

# Show result
print("\nFinal result:")
r = requests.get(f'{BASE_URL}/outputs/jobs/{job_id}', headers=headers)
result = r.json()['data']
print(f"  Status: {result['status']}")
print(f"  Attempts: {result['attempts']}")
if result.get('last_error'):
    print(f"  Error: {result['last_error']}")
if result.get('payload'):
    p = result['payload']
    print(f"  Product: {p.get('product_name')}")
    print(f"  SKU: {p.get('sku')}")
    print(f"  Price: {p.get('currency')} {p.get('price')}")
    print(f"  Base Price: {p.get('base_price')}")
    print(f"  Saving: {p.get('currency')} {p.get('saving')}")
    print(f"  Stock: {p.get('stock_qty')}")
    print(f"  Store: {p.get('store_name')}")
    if p.get('qr_text'):
        print(f"\n  QR LINK (what customer's phone opens when scanning):")
        print(f"  ---")
        print(f"  {p['qr_text']}")
        print(f"  ---")
    if p.get('qr_image_base64'):
        img_data = base64.b64decode(p['qr_image_base64'])
        with open("C:/Users/dell/Desktop/price inteli/qr_output.png", "wb") as f:
            f.write(img_data)
        print(f"\n  QR Image saved! ({len(img_data)} bytes)")
        print("  Open qr_output.png on Desktop to see the QR code")
else:
    print("  No payload yet")
print("\nDone!")
