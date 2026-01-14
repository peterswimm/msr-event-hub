import requests

try:
    resp = requests.get("http://localhost:8000/api/chat/welcome", timeout=5)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Keys: {data.keys()}")
        print(f"Has adaptive_card: {'adaptive_card' in data}")
        if "adaptive_card" in data:
            card = data["adaptive_card"]
            if card:
                print(f"Card type: {card.get('type')}")
                print(f"Card has body: {'body' in card}")
            else:
                print("Card is None!")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Failed: {e}")
