from models import db, Admin
from werkzeug.security import generate_password_hash
from datetime import datetime
from dotenv import load_dotenv 
import os


load_dotenv()


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


if __name__ == "__main__":
    from app import app

    with app.app_context():
        db.create_all()
        create_superuser()
