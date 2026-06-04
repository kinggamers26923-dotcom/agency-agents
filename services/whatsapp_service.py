import requests
from requests.auth import HTTPBasicAuth


def send_message(account_sid: str, auth_token: str, from_number: str, to_number: str, body: str) -> dict:
    """Send a WhatsApp message via Twilio REST API."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = {"From": f"whatsapp:{from_number}", "To": f"whatsapp:{to_number}", "Body": body}
    resp = requests.post(url, data=data, auth=HTTPBasicAuth(account_sid, auth_token), timeout=10)
    resp.raise_for_status()
    return resp.json()


def send_media_message(account_sid: str, auth_token: str, from_number: str, to_number: str, body: str, media_url: str) -> dict:
    """Send a WhatsApp media message via Twilio REST API."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = {
        "From": f"whatsapp:{from_number}",
        "To": f"whatsapp:{to_number}",
        "Body": body,
        "MediaUrl": media_url,
    }
    resp = requests.post(url, data=data, auth=HTTPBasicAuth(account_sid, auth_token), timeout=20)
    resp.raise_for_status()
    return resp.json()
