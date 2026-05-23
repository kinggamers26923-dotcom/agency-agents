from flask_sqlalchemy import SQLAlchemy
import datetime
import uuid

db = SQLAlchemy()

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = db.Column(db.String(20), nullable=False) # 'telegram', 'whatsapp'
    sender = db.Column(db.String(100), nullable=False)  # User ID or Phone Number
    body = db.Column(db.Text, nullable=False)
    is_inbound = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='received') # received, ai_processing, pending_approval, approved, sent, ignored
    response = db.Column(db.Text, nullable=True) # The AI's drafted response
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "platform": self.platform,
            "sender": self.sender,
            "body": self.body,
            "is_inbound": self.is_inbound,
            "status": self.status,
            "response": self.response,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "sent_at": self.sent_at.isoformat() + "Z" if self.sent_at else None
        }
