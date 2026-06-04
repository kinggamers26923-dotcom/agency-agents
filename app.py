import os
import uuid
import datetime
import threading
from flask import Flask, request, jsonify, render_template, make_response
from dotenv import load_dotenv

load_dotenv(override=True)

from services.telegram_service import send_message as telegram_send
from services.whatsapp_service import send_message as whatsapp_send
from services.ai_service import process_inbound_message
from services.desktop_service import handle_command, search_local_files
from models import db, Message

APP_ENV = os.getenv("APP_ENV", "development")

app = Flask(__name__)
# Configure database from environment, fallback to SQLite for local/demo use
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///jarvis.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"connect_args": {"check_same_thread": False}}

db.init_app(app)

# Simple in-memory task list used by the standalone UI page
TASKS = []
TASK_LOCK = threading.Lock()

with app.app_context():
    db.create_all()

ALLOWED_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}

@app.before_request
def handle_cors_preflight():
    origin = request.headers.get('Origin')
    if request.method == 'OPTIONS':
        response = make_response()
        if origin in ALLOWED_ORIGINS:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/ai-assistant", methods=["GET"])
def ai_assistant():
    return render_template("ai-assistant.html")

@app.route("/jarvis-os", methods=["GET"])
def jarvis_os():
    return render_template("jarvis-os.html")

@app.route("/api/tasks", methods=["GET", "POST"])
def api_tasks():
    if request.method == "GET":
        return jsonify({"tasks": TASKS})

    payload = request.get_json(force=True) or {}
    title = str(payload.get("title", "")).strip()
    if not title:
        return jsonify({"error": "Missing title"}), 400

    task = {"id": str(uuid.uuid4()), "title": title}
    with TASK_LOCK:
        TASKS.append(task)
    return jsonify(task), 201

@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    with TASK_LOCK:
        for index, task in enumerate(TASKS):
            if task["id"] == task_id:
                TASKS.pop(index)
                return jsonify({"success": True})
    return jsonify({"error": "Task not found"}), 404

@app.route("/api/jarves", methods=["POST"])
def api_jarves():
    payload = request.get_json(force=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Missing message"}), 400

    try:
        reply = process_inbound_message(message, "web", "local_user")
        return jsonify({"reply": reply})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

@app.route("/api/status", methods=["GET"])
def api_status():
    pending_count = Message.query.filter_by(status='pending_approval').count()
    sent_count = Message.query.filter_by(status='sent').count()
    received_count = Message.query.filter_by(status='received').count()
    return jsonify({
        "pending_approval_count": pending_count,
        "sent_count": sent_count,
        "received_count": received_count
    })

@app.route("/api/search", methods=["GET"])
def api_search():
    query = str(request.args.get("q", "")).strip()
    if not query:
        return jsonify({"error": "Missing query parameter q"}), 400

    results = search_local_files(query)
    return jsonify({"files": results})

@app.route("/api/messages", methods=["GET"])
def api_messages():
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return jsonify([message.to_dict() for message in messages])

@app.route("/api/messages/<message_id>/approve", methods=["POST"])
def api_approve_message(message_id):
    msg = db.session.get(Message, message_id)
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
            res = whatsapp_send(account_sid, auth_token, from_number, msg.sender, send_text)
        else:
            return jsonify({"error": "Unsupported platform"}), 400

        msg.status = 'sent'
        msg.sent_at = datetime.datetime.utcnow()
        db.session.commit()
        return jsonify({"success": True, "response": res})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


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

@app.route("/api/command", methods=["POST"])
def run_command():
    payload = request.get_json(force=True)
    if not payload or "command" not in payload:
        return jsonify({"success": False, "message": "Invalid payload, require command"}), 400

    command_text = payload.get("command", "").strip()
    if not command_text:
        return jsonify({"success": False, "message": "Command cannot be empty."}), 400

    result = handle_command(command_text)
    return jsonify(result)

@app.route("/api/draft", methods=["POST"])
def draft_message():
    """Create an AI-drafted reply and queue it for owner approval."""
    payload = request.get_json(force=True)
    if not payload or "platform" not in payload or "body" not in payload:
        return jsonify({"error": "Invalid payload, require platform/body"}), 400

    platform = normalize_platform(payload["platform"])
    if platform not in ("telegram", "whatsapp"):
        return jsonify({"error": "Unsupported platform, must be telegram or whatsapp"}), 400

    sender = payload.get("sender") or payload.get("from") or "local_user"
    msg = Message(
        platform=platform,
        sender=str(sender),
        body=payload["body"],
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
