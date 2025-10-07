#!/usr/bin/env python3
import os
import requests

api_url = os.getenv('CHOREO_API_SERVICE_CONNECTION_SERVICEURL')
api_key = os.getenv('CHOREO_API_SERVICE_CONNECTION_APIKEY')

print(f'API URL: {api_url}')
print(f'API Key: {api_key[:20]}...' if api_key else 'No API Key')
print()

headers = {'API-Key': api_key} if api_key else {}

# Call root endpoint
print('=== Root Endpoint ===')
try:
    resp = requests.get(api_url, headers=headers, timeout=10)
    print(f'Status: {resp.status_code}')
    print(resp.text)
except Exception as e:
    print(f'Error: {e}')
print()

# Call posts endpoint
print('=== Posts Endpoint ===')
try:
    resp = requests.get(f'{api_url}posts', headers=headers, timeout=10)
    print(f'Status: {resp.status_code}')
    print(resp.text[:500] if len(resp.text) > 500 else resp.text)
except Exception as e:
    print(f'Error: {e}')
print()

# Call sentiment stats
print('=== Sentiment Stats ===')
try:
    resp = requests.get(f'{api_url}sentiment/stats', headers=headers, timeout=10)
    print(f'Status: {resp.status_code}')
    print(resp.text)
except Exception as e:
    print(f'Error: {e}')
