import os
import uuid
import datetime
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv(override=True)

from services.telegram_service import send_message as telegram_send
from services.whatsapp_service import send_message as whatsapp_send
from services.ai_service import process_inbound_message
from models import db, Message

APP_ENV = os.getenv("APP_ENV", "development")

app = Flask(__name__)
# Configure database from environment, fallback to SQLite for local/demo use
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///jarvis.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"connect_args": {"check_same_thread": False}}

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/", methods=["GET"])
def index():
    pending_count = Message.query.filter_by(status='pending_approval').count()
    sent_count = Message.query.filter_by(status='sent').count()
    return jsonify({"pending_approval_count": pending_count, "sent_count": sent_count})

def normalize_platform(platform_value: str) -> str:
    if not platform_value:
        return "unknown"
    return platform_value.strip().lower()


def handle_inbound_background(message_id):
    """Background task to generate AI response and set status to pending_approval"""
    with app.app_context():
        msg = db.session.get(Message, message_id)
        if not msg:
            return
        
        msg.status = 'ai_processing'
        db.session.commit()

        try:
            ai_draft = process_inbound_message(msg.body, msg.platform, msg.sender)
            msg.response = ai_draft
            msg.status = 'pending_approval'
            
            # FUTURE VISION: Here we could trigger a push notification to the owner's app/phone 
            # to say "Jarvis drafted a reply to {msg.sender}. Approve?"
            
        except Exception as e:
            print(f"AI Processing error: {e}")
            msg.response = "I'm sorry, I could not generate the response automatically. Please retry later or review manually."
            msg.status = 'pending_approval'
        
        db.session.commit()

@app.route("/queue", methods=["POST"])
def queue_message():
    """Manually queue a message for sending (bypassing AI generation)"""
    payload = request.get_json(force=True)
    if not payload or "platform" not in payload or "to" not in payload or "body" not in payload:
        return jsonify({"error": "Invalid payload, require platform/to/body"}), 400

    platform = normalize_platform(payload["platform"])
    if platform not in ("telegram", "whatsapp"):
        return jsonify({"error": "Unsupported platform, must be telegram or whatsapp"}), 400

    msg = Message(
        platform=platform,
        sender=payload["to"],  # Target contact for outbound message
        body=payload["body"],
        is_inbound=False,
        status='pending_approval'
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify(msg.to_dict()), 201

@app.route("/pending", methods=["GET"])
def list_pending():
    """List all messages waiting for owner approval"""
    pending = Message.query.filter_by(status='pending_approval').all()
    return jsonify([p.to_dict() for p in pending])

@app.route("/approve", methods=["POST"])
def approve_and_send():
    """Owner approves an AI-drafted message to be sent"""
    payload = request.get_json(force=True)
    msg_id = payload.get("id")
    if not msg_id:
        return jsonify({"error": "Missing id"}), 400

    msg = db.session.get(Message, msg_id)
    if not msg:
        return jsonify({"error": "Message not found"}), 404
    
    if msg.status != 'pending_approval':
        return jsonify({"error": f"Message is not pending approval, current status is {msg.status}"}), 400

    try:
        send_text = msg.response or msg.body
        if msg.platform == "telegram":
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = msg.sender
            res = telegram_send(token, chat_id, send_text)
        elif msg.platform == "whatsapp":
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            from_number = os.getenv("TWILIO_WHATSAPP_FROM")
            to_number = msg.sender
            res = whatsapp_send(account_sid, auth_token, from_number, to_number, send_text)
        else:
            return jsonify({"error": "Unsupported platform"}), 400

        msg.status = 'sent'
        msg.sent_at = datetime.datetime.utcnow()
        db.session.commit()
        return jsonify(msg.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/webhook/telegram", methods=["POST"])
def webhook_telegram():
    data = request.get_json(force=True)
    message = data.get("message") or data
    
    sender_id = message.get("from", {}).get("id") if isinstance(message, dict) else None
    body = message.get("text") if isinstance(message, dict) else str(message)
    
    if not sender_id or not body:
         return jsonify({"ok": True, "note": "ignored empty/invalid message"})

    msg = Message(
        platform="telegram",
        sender=str(sender_id),
        body=body,
        is_inbound=True,
        status='received'
    )
    db.session.add(msg)
    db.session.commit()
    
    # Process AI in background so webhook returns 200 immediately
    thread = threading.Thread(
        target=handle_inbound_background,
        args=(msg.id,),
        daemon=True
    )
    thread.start()
    
    return jsonify({"ok": True})

@app.route("/webhook/whatsapp", methods=["POST"])
def webhook_whatsapp():
    data = request.form or request.get_json(silent=True) or {}
    from_number = data.get("From")
    body = data.get("Body")
    
    if not from_number or not body:
         return ("", 204)

    msg = Message(
        platform="whatsapp",
        sender=from_number,
        body=body,
        is_inbound=True,
        status='received'
    )
    db.session.add(msg)
    db.session.commit()
    
    thread = threading.Thread(
        target=handle_inbound_background,
        args=(msg.id,),
        daemon=True
    )
    thread.start()
    
    return ("", 204)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=(APP_ENV != "production"))
