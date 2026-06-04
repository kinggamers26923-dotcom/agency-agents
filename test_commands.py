import urllib.request, json

tests = [
    {'command': 'open youtube.com'},
    {'command': 'search file report'},
    {'command': 'what is the weather'}
]

for test in tests:
    try:
        req = urllib.request.Request(
            'http://127.0.0.1:5000/api/command',
            method='POST',
            data=json.dumps(test).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read().decode())
            print(f"Command: {test['command']}")
            print(f"  Success: {resp.get('success')}, Action: {resp.get('action')}")
            print(f"  Message: {resp.get('message')[:80]}")
    except Exception as e:
        print(f"ERROR on {test['command']}: {e}")
    print()
