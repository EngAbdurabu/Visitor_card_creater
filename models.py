from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class EVENT(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    event_time = db.Column(db.DateTime, nullable=False)

    cards = db.relationship("CARD", backref="event", lazy=True)
    invitations = db.relationship("Invitation", backref="event", lazy=True)


class CARD(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_filename = db.Column(db.String(100))
    message = db.Column(db.Text)
    card_no = db.Column(db.Integer, nullable=False)  # عدد الدعوات
    event_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)

    invitations = db.relationship("Invitation", backref="card", lazy=True)


class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_token = db.Column(db.String(100), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey("card.id"), nullable=False)

    visitor_id = db.Column(db.Integer, db.ForeignKey("visitor.id"))


class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(14))
    image_filename = db.Column(db.String(100))
    qr_filename = db.Column(db.String(100))
    qr_token = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed = db.Column(db.Boolean, default=False)
    attended = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6))  # رمز التحقق
    otp_created_at = db.Column(db.DateTime)  # وقت إنشاء الرمز
    is_verified = db.Column(db.Boolean, default=False)  # هل تم التحقق من البريد؟
    invitation = db.relationship("Invitation", backref="visitor", uselist=False)
