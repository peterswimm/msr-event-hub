import requests
import json
import sys

url = "http://localhost:8000/api/chat/stream"
payload = {"messages": [{"role": "user", "content": "Browse All Projects"}]}

print("Testing streaming endpoint...")
print(f"URL: {url}")
print()

try:
    response = requests.post(url, json=payload, stream=True, timeout=30)
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code != 200:
        print(f"ERROR: {response.text}")
        sys.exit(1)
    
    print("Receiving stream events...")
    print()
    
    event_count = 0
    card_found = False
    
    for line in response.iter_lines():
        if not line:
            continue
        
        line = line.decode('utf-8') if isinstance(line, bytes) else line
        
        if line.startswith("data:"):
            event_count += 1
            data = line[5:].strip()
            
            if data == "[DONE]":
                print(f"✓ Received [DONE]")
                break
            
            try:
                event = json.loads(data)
                has_card = "adaptive_card" in event and event["adaptive_card"] is not None
                has_delta = "delta" in event and event["delta"]
                
                if has_card:
                    card_found = True
                    print(f"✓ Event {event_count}: ADAPTIVE CARD FOUND")
                    print(f"  - Card type: {event['adaptive_card'].get('type')}")
                    print(f"  - Has body: {'body' in event['adaptive_card']}")
                elif has_delta:
                    print(f"  Event {event_count}: Text delta ({len(event['delta'])} chars)")
            except json.JSONDecodeError as e:
                print(f"✗ Failed to parse event {event_count}: {e}")
                print(f"  Data: {data[:100]}...")
    
    print()
    print("=" * 50)
    if card_found:
        print("✓✓✓ SUCCESS: Adaptive card received in stream!")
    else:
        print("✗✗✗ FAILURE: No adaptive card in stream")
    print("=" * 50)
    
except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to server on http://localhost:8000")
    print("Make sure the server is running")
except Exception as e:
    print(f"ERROR: {e}")
