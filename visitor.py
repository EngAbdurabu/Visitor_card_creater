from flask import (
    Blueprint,
    redirect,
    url_for,
    render_template,
    request,
    flash,
    current_app,
)
import os, qrcode, secrets
from weasyprint import HTML
from flask_mail import Mail, Message
from models import *
from datetime import datetime, timedelta

bp = Blueprint("visitor", __name__, url_prefix="/visitor")
mail = Mail()


@bp.route("/register/<token>", methods=["GET", "POST"])
def register(token):
    invitation = Invitation.query.filter_by(unique_token=token).first()
    if not invitation:
        flash("رابط الدعوة غير صالح", "danger")
        return redirect(url_for("visitor.invitation"))

    if invitation.is_used:
        flash("هذه الدعوة تم استخدامها مسبقاً", "warning")
        return redirect(url_for("visitor.invitation"))

    card = invitation.card
    event = invitation.event

    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        photo = request.files["photo"]

        if Visitor.query.filter_by(email=email).first():
            flash("هذا البريد الإلكتروني مسجل مسبقًا.", "warning")
            return redirect(url_for("visitor.invitation"))

        visitor = Visitor(full_name=full_name, email=email, phone=phone)

        if photo and photo.filename:
            photo_filename = f"{datetime.now().timestamp()}_{photo.filename}"
            photo_filepath = os.path.join(
                current_app.config["UPLOAD_FOLDER"], photo_filename
            )
            photo.save(photo_filepath)
            visitor.image_filename = photo_filename

        qr_token = secrets.token_urlsafe(16)
        visitor.qr_token = qr_token

        otp = f"{secrets.randbelow(1000000):06d}"
        visitor.otp = otp
        visitor.otp_created_at = datetime.utcnow()
        visitor.is_verified = False

        db.session.add(visitor)
        db.session.commit()

        invitation.visitor_id = visitor.id
        db.session.commit()

        # إرسال OTP
        msg = Message(
            "رمز التحقق من بريدك الإلكتروني",
            sender=current_app.config["MAIL_USERNAME"],
            recipients=[visitor.email],
        )
        msg.body = f"""
مرحباً {visitor.full_name}،

رمز التحقق الخاص بك هو: {otp}

يرجى إدخاله لتأكيد البريد الإلكتروني ومتابعة استلام بطاقة الدعوة.

الرمز صالح لمدة 10 دقائق فقط.
"""
        mail.send(msg)

        return redirect(url_for("visitor.verify_otp", visitor_id=visitor.id))

    return render_template("visitor/register.html", event=event, card=card)


@bp.route("/verify_otp/<int:visitor_id>", methods=["GET", "POST"])
def verify_otp(visitor_id):
    visitor = Visitor.query.get_or_404(visitor_id)

    if request.method == "POST":
        entered_otp = request.form["otp"]

        if (
            visitor.otp == entered_otp
            and datetime.utcnow() - visitor.otp_created_at <= timedelta(minutes=10)
        ):
            visitor.is_verified = True
            db.session.commit()

            flash(
                "✅ تم التحقق من البريد بنجاح. سيتم الآن إرسال بطاقة الدعوة.", "success"
            )

            invitation = visitor.invitation
            event = invitation.event
            card = invitation.card

            confirm_url = url_for(
                "visitor.confirm_attendance", token=visitor.qr_token, _external=True
            )
            qr_img = qrcode.make(confirm_url)
            qr_filename = f"qr_{visitor.id}.png"
            qr_path = os.path.join(current_app.config["UPLOAD_FOLDER"], qr_filename)
            qr_img.save(qr_path)

            visitor.qr_filename = qr_filename
            invitation.is_used = True
            db.session.commit()

            pdf_path = generate_pdf(visitor, event, card, confirm_url)
            send_visitor_email(visitor, event, pdf_path)

            return redirect(url_for("visitor.invitation"))
        else:
            flash("❌ رمز التحقق غير صحيح أو منتهي الصلاحية", "danger")

    return render_template("visitor/verify_otp.html", visitor=visitor)


@bp.route("/invitation/done")
def invitation():
    return render_template("visitor/done.html")


@bp.route("/confirm_attendance/<token>")
def confirm_attendance(token):
    visitor = Visitor.query.filter_by(qr_token=token).first()
    if visitor:
        visitor.attended = True
        db.session.commit()

        invitation = visitor.invitation
        event = invitation.event if invitation else None
        return render_template("visitor/confirmed.html", visitor=visitor, event=event)
    else:
        return "رمز غير صالح", 404


def generate_pdf(visitor, event, card, confirm_url):
    pdf_filename = f"invitation_{visitor.id}.pdf"
    pdf_path = os.path.join(current_app.config["UPLOAD_FOLDER"], pdf_filename)

    image_url = (
        url_for("static", filename=f"uploads/{visitor.image_filename}", _external=True)
        if visitor.image_filename
        else None
    )
    qr_url = (
        url_for("static", filename=f"uploads/{visitor.qr_filename}", _external=True)
        if visitor.qr_filename
        else None
    )
    card_image_url = (
        url_for("static", filename=f"uploads/{card.image_filename}", _external=True)
        if card.image_filename
        else None
    )

    html = render_template(
        "visitor/invitation_pdf.html",
        visitor=visitor,
        event=event,
        card=card,
        visitor_image=image_url,
        qr_image=qr_url,
        card_image=card_image_url,
        confirm_url=confirm_url,
    )

    base_url = request.host_url
    HTML(string=html, base_url=base_url).write_pdf(pdf_path)

    return pdf_path


def send_visitor_email(visitor, event, pdf_path):
    msg = Message(
        f"دعوتك لحضور {event.name}",
        sender=current_app.config["MAIL_USERNAME"],
        recipients=[visitor.email],
    )
    msg.body = f"""
مرحباً {visitor.full_name},

يسعدنا دعوتك لحضور {event.name} في تاريخ {event.event_time.strftime('%Y-%m-%d')}.

تجد بطاقة الدعوة مرفقة مع هذا البريد.

مع أطيب التحيات
"""

    with current_app.open_resource(pdf_path) as pdf:
        msg.attach(f"invitation_{visitor.id}.pdf", "application/pdf", pdf.read())

    mail.send(msg)
