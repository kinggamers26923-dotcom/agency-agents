import requests
import time
import uuid

print("="*40)
print("     JARVIS LOCAL TEST TERMINAL")
print("="*40)
print("Type 'exit' to quit.\n")

while True:
    try:
        msg = input("You: ")
        if msg.lower() in ['quit', 'exit']:
            break
        
        # Simulate a unique telegram user
        sender_id = "test_user_" + str(uuid.uuid4())[:4]
        
        payload = {
            "message": {
                "from": {"id": sender_id},
                "text": msg
            }
        }
        
        print("Jarvis is thinking (Sending to webhook)...")
        requests.post("http://localhost:5000/webhook/telegram", json=payload)
        
        # Wait a few seconds for Gemini to generate the draft
        time.sleep(4)
        
        # Check the pending queue
        resp = requests.get("http://localhost:5000/pending")
        if resp.status_code == 200:
            data = resp.json()
            found = False
            for item in data:
                if item['sender'] == sender_id:
                    print(f"\n[DRAFT AWAITING APPROVAL]")
                    print(f"Jarvis: {item['response']}\n")
                    found = True
                    break
            
            if not found:
                print("\n[Error: Message not found in pending queue. Check server logs.]\n")
        else:
            print("Error connecting to server.")
            
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error: {e}")
