#!/usr/bin/env python
"""Test the chat API browse_all endpoint."""
import sys
import json
sys.path.insert(0, '.')

# Create test app
from main import create_app
app = create_app()

# Create a test client
from fastapi.testclient import TestClient
client = TestClient(app)

# Test the browse_all action
response = client.post(
    "/api/chat/stream",
    json={
        "messages": [
            {
                "role": "user",
                "content": json.dumps({
                    "type": "browse_all",
                    "action": "browse_all"
                })
            }
        ]
    }
)

print(f"Response status: {response.status_code}")
print(f"Response headers: {dict(response.headers)}")

if response.status_code == 200:
    # Parse SSE response
    lines = response.text.split('\n')
    print(f"Response lines: {len(lines)}")
    print(f"\nRaw response (first 2000 chars):\n{response.text[:2000]}\n")
    
    for i, line in enumerate(lines):
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if "adaptive_card" in data:
                    card = data["adaptive_card"]
                    print(f"\n✓ Found adaptive_card in line {i}")
                    print(f"  - Type: {card.get('type')}")
                    print(f"  - Version: {card.get('version')}")
                    print(f"  - Body items: {len(card.get('body', []))}")
                    print(f"  - Actions: {len(card.get('actions', []))}")
                    
                    # Print body summary
                    body = card.get('body', [])
                    print(f"\n  Body structure:")
                    for j, item in enumerate(body[:5]):
                        print(f"    [{j}] type={item.get('type')}, text={item.get('text', '')[:50]}")
                    
                    # Print first project container
                    if len(body) > 2:
                        first_proj = body[2]
                        if first_proj.get('type') == 'Container':
                            items = first_proj.get('items', [])
                            print(f"\n  First project details:")
                            for item in items:
                                print(f"    - {item.get('text', '')[:80]}")
            except json.JSONDecodeError as e:
                print(f"Could not parse JSON from line {i}: {str(e)[:100]}")
else:
    print(f"Error response: {response.text[:500]}")
