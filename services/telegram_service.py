import requests


def send_message(token: str, chat_id: str, text: str) -> dict:
    """Send a Telegram message using Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    resp = requests.post(url, data=data, timeout=10)
    resp.raise_for_status()
    return resp.json()
