import argparse
import json
import requests
import os

BASE = os.getenv("BASE_URL", "http://localhost:5000")


def queue(platform, to, body):
    url = f"{BASE}/queue"
    payload = {"platform": platform, "to": to, "body": body}
    r = requests.post(url, json=payload)
    print(r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)


def list_pending():
    url = f"{BASE}/pending"
    r = requests.get(url)
    print(r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)


def approve(msg_id):
    url = f"{BASE}/approve"
    r = requests.post(url, json={"id": msg_id})
    print(r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Simple CLI for local messaging app")
    sub = p.add_subparsers(dest="cmd")

    q = sub.add_parser("queue")
    q.add_argument("platform", choices=["telegram", "whatsapp"])
    q.add_argument("to")
    q.add_argument("body")

    l = sub.add_parser("list")

    a = sub.add_parser("approve")
    a.add_argument("id")

    args = p.parse_args()

    if args.cmd == "queue":
        queue(args.platform, args.to, args.body)
    elif args.cmd == "list":
        list_pending()
    elif args.cmd == "approve":
        approve(args.id)
    else:
        p.print_help()
