from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    g,
    current_app,
)
from werkzeug.security import generate_password_hash, check_password_hash
from models import *
from datetime import datetime
from helper import login_required_admin
import os

bp = Blueprint(__name__, "auth", url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("event_id")  # أو admin_id حسب مشروعك
    if user_id is None:
        g.user = None
    else:
        g.user = EVENT.query.get(user_id)


@bp.route("/event_register", methods=["GET", "POST"])  # type: ignore
@login_required_admin
def event_register():
    if request.method == "POST":
        event_name = request.form["event_name"]
        event_email = request.form["event_email"]
        event_password = request.form["event_password"]
        event_time = request.form["event_time"]

        # تحويل النص إلى كائن datetime
        try:
            event_time = datetime.strptime(event_time, "%Y-%m-%d")
        except ValueError:
            # لو المستخدم أدخل تاريخ غير صالح
            return "Invalid date format. Please use YYYY-MM-DD.", 400

        # register event
        event = EVENT(name=event_name, email=event_email, password=generate_password_hash(event_password), event_time=event_time)  # type: ignore
        # add and save session
        db.session.add(event)
        db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template("auth/event_register.html")


@bp.route("/login", methods=["GET", "POST"])  # type: ignore
def login():
    if request.method == "POST":
        email = request.form.get("event_email")
        password = request.form.get("event_password")

        event = EVENT.query.filter_by(email=email).first()

        if event and check_password_hash(event.password, password):  # type: ignore
            session["event_id"] = event.id
            flash("تم تسجيل الدخول بنجاح", "success")
            return redirect(
                url_for("card.event_dashboard")
            )  # ضع اسم الراوت الخاص بالداشبورد
        else:
            flash("بيانات الدخول غير صحيحة", "danger")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@bp.route("/delete_all", methods=["POST"])
@login_required_admin
def delete_all_data():
    try:
        # حذف الصور المرتبطة بالبطاقات
        events = EVENT.query.all()
        for event in events:
            for card in event.cards:
                if card.image_filename:
                    image_path = os.path.join(current_app.static_folder, "uploads", card.image_filename)  # type: ignore
                    if os.path.exists(image_path):
                        os.remove(image_path)

        # حذف صور الزوار و QR و ملفات PDF
        visitors = Visitor.query.all()
        for visitor in visitors:
            # صورة الزائر
            if visitor.photo:
                photo_path = os.path.join(current_app.static_folder, "uploads", visitor.photo)  # type: ignore
                if os.path.exists(photo_path):
                    os.remove(photo_path)

            # رمز QR
            if visitor.qr_filename:
                qr_path = os.path.join(current_app.static_folder, "uploads", visitor.qr_filename)  # type: ignore
                if os.path.exists(qr_path):
                    os.remove(qr_path)

            # ملف PDF
            pdf_filename = f"invitation_{visitor.id}.pdf"
            pdf_path = os.path.join(current_app.static_folder, "uploads", pdf_filename)  # type: ignore
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        # حذف البيانات من قاعدة البيانات
        db.session.query(Visitor).delete()
        db.session.query(Invitation).delete()
        db.session.query(CARD).delete()
        db.session.query(EVENT).delete()
        db.session.commit()

        flash("✅ تم حذف كل البيانات والصور والملفات المرتبطة بنجاح.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"❌ حدث خطأ أثناء الحذف: {e}", "danger")

    return redirect(url_for("index"))
