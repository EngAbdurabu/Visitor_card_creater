from flask import (
    session,
    Blueprint,
    flash,
    redirect,
    url_for,
    render_template,
    request,
    current_app,
    g,
)
from flask_mail import Message
from helper import login_required_event
from datetime import datetime
import os
import secrets
from models import *

bp = Blueprint("card", __name__, url_prefix="/event")


@bp.route("/dashboard")
@login_required_event
def event_dashboard():
    if "event_id" not in session:
        flash("يجب تسجيل الدخول أولاً", "warning")
        return redirect(url_for("auth.login"))

    event_id = session["event_id"]
    event = EVENT.query.get(event_id)
    cards = CARD.query.filter_by(event_id=event_id).all()

    return render_template("card/dashboard.html", event=event, cards=cards)


@bp.route("/card_maker", methods=["POST", "GET"])
@login_required_event
def card_maker():
    if request.method == "POST":
        name = request.form["event_name"]
        message = request.form["message"]
        card_no = int(request.form["card_no"])
        event_time = request.form["event_time"]
        photo = request.files["photo"]

        try:
            event_time = datetime.strptime(event_time, "%Y-%m-%d")
        except ValueError:
            flash("صيغة التاريخ غير صحيحة", "danger")
            return redirect(url_for("card.card_maker"))

        photo_filename = f"{datetime.now().timestamp()}_{photo.filename}"
        photo_filepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"], photo_filename
        )
        photo.save(photo_filepath)

        event_id = session["event_id"]
        card = CARD(
            name=name,
            image_filename=photo_filename,
            message=message,
            card_no=card_no,
            event_time=event_time,
            event_id=event_id,
        )
        db.session.add(card)
        db.session.commit()

        for i in range(card_no):
            invitation = Invitation(
                unique_token=secrets.token_urlsafe(32),
                event_id=event_id,
                card_id=card.id,
            )
            db.session.add(invitation)

        db.session.commit()
        flash(f"تم إنشاء البطاقة و {card_no} دعوة بنجاح!", "success")
        return redirect(url_for("card.card_show"))

    return render_template("card/card_maker.html")


@bp.route("/card-show")
@login_required_event
def card_show():
    event_id = session["event_id"]
    cards = CARD.query.filter_by(event_id=event_id).all()
    return render_template("card/card_show.html", cards=cards)


@bp.route("/invitations/<int:card_id>")
@login_required_event
def show_invitations(card_id):
    card = CARD.query.get_or_404(card_id)
    if card.event_id != session["event_id"]:
        flash("ليس لديك صلاحية لعرض هذه الدعوات", "danger")
        return redirect(url_for("card.event_dashboard"))

    invitations = Invitation.query.filter_by(card_id=card_id).all()
    return render_template("card/invitations.html", card=card, invitations=invitations)


@bp.route("/visitor-info")
@login_required_event
def visitor_info():
    event_id = session["event_id"]
    visitors = (
        db.session.query(Visitor)
        .join(Invitation)
        .filter(Invitation.event_id == event_id, Invitation.visitor_id.isnot(None))
        .all()
    )

    return render_template("card/visitor_info.html", visitors=visitors)


@bp.route("/qr-scanning")
@login_required_event
def qr_scanning():
    return render_template("card/scanner.html")


# api to send invaition
@bp.route("/send_invitations/<int:card_id>", methods=["POST"])
@login_required_event
def send_invitations(card_id):
    card = CARD.query.get_or_404(card_id)

    if card.event_id != session["event_id"]:
        return {"error": "غير مصرح"}, 403

    emails = request.json.get("emails", [])
    invitations = (
        Invitation.query.filter_by(card_id=card_id, is_used=False)
        .limit(len(emails))
        .all()
    )

    if len(invitations) < len(emails):
        return {"error": "عدد الإيميلات أكبر من الدعوات المتاحة"}, 400

    for email, invitation in zip(emails, invitations):
        send_invitation_email(email, invitation, card)

    return {"success": True, "sent": len(emails)}


def send_invitation_email(email, invitation, card):
    event = card.event
    invitation_url = url_for(
        "visitor.register", token=invitation.unique_token, _external=True
    )

    msg = Message(
        f"دعوة لحضور {event.name}",
        sender=current_app.config["MAIL_USERNAME"],
        recipients=[email],
    )

    msg.html = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif;">
        <h2>دعوة خاصة</h2>
        <p>يسرنا دعوتكم لحضور {event.name}</p>
        <p><strong>التاريخ:</strong> {event.event_time.strftime('%Y-%m-%d')}</p>
        <p>{card.message}</p>
        <p>
            <a href="{invitation_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                التسجيل وتأكيد الحضور
            </a>
        </p>
        <p>نتطلع لرؤيتكم في الحدث</p>
    </div>
    """

    email.send(msg)
