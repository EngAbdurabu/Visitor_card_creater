from flask import Flask, render_template, redirect, url_for, session, flash, request, g
from auth import bp as authbp
from card import bp as cardbp
from visitor import bp as visitorbp, mail
from models import *
import os
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from helper import login_required_admin


load_dotenv()

app = Flask(__name__)

# إعداد المسارات وقاعدة البيانات
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///event.db"
app.config["UPLOAD_FOLDER"] = "static/uploads/"
app.config["SECRET_KEY"] = os.getenv("app_secret_key")

# إعداد البريد
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

# register Blueprint
app.register_blueprint(authbp)
app.register_blueprint(cardbp)
app.register_blueprint(visitorbp)


# تهيئة الإضافات
db.init_app(app)
mail.init_app(app)


# إنشاء مجلد رفع الصور لو غير موجود
# --------------------------------------
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def create_superuser():
    name = os.getenv("admin_username")
    email = os.getenv("MAIL_USERNAME")
    password = os.getenv("admin_password")  # غيّره لكلمة قوية
    event_time = datetime.strptime("2025-12-31", "%Y-%m-%d")

    # تحقق لو موجود بالفعل
    existing_admin = Admin.query.filter_by(email=email).first()
    if existing_admin:
        print("⚠️ الـ Superuser موجود بالفعل.")
        return

    hashed_password = generate_password_hash(password)
    admin = Admin(name=name, email=email, password=hashed_password)  # type: ignore

    db.session.add(admin)
    db.session.commit()
    print("✅ Superuser تم إنشاؤه بنجاح.")


@app.route("/")
def index():
    event = EVENT.query.all()
    return render_template("index.html", events=event)


# Context لتحميل المستخدم
@app.before_request
def load_logged_in_user():
    admin_id = session.get("admin_id")
    if admin_id is None:
        g.admin = None
    else:
        g.admin = Admin.query.get(admin_id)


# مسار تسجيل الدخول
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        admin = Admin.query.filter_by(name=username).first()

        if admin and check_password_hash(admin.password, password):
            session.clear()
            session["admin_id"] = admin.id
            return redirect(url_for("auth.event_register"))
        else:
            flash("❌ أسم المستخدم او كلمة المرور غير صحيحة ", "danger")

    return render_template("admin_login.html")


# مسار تسجيل الخروج
@app.route("/admin/logout")
@login_required_admin
def admin_logout():
    session.clear()
    flash("✅ تم تسجيل الخروج بنجاح", "success")
    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ينشئ الجداول لو مش موجودة
        create_superuser()
    app.run()
