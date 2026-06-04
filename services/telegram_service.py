import requests


def send_message(token: str, chat_id: str, text: str) -> dict:
    """Send a Telegram message using Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    resp = requests.post(url, data=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def send_document(token: str, chat_id: str, file_path: str, caption: str = None) -> dict:
    """Send a local file to a Telegram chat using Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    data = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption
    with open(file_path, "rb") as document:
        files = {"document": document}
        resp = requests.post(url, data=data, files=files, timeout=30)
    resp.raise_for_status()
    return resp.json()
