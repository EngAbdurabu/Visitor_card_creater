# 🎉 Flask Event Invitation Management System

A powerful web-based platform to create, manage, and send electronic invitations for events. Built using **Flask**, **Bootstrap**, and **SQLite**, this system supports both admin and event manager roles, OTP email verification, PDF generation, QR code-based attendance, and automatic event cleanup after expiry.

---

## 🚀 Features

- 👤 Superuser (Admin) dashboard to manage event accounts
- 🗓️ Event owner role to create cards and invitations
- ✉️ Invitation email with PDF and QR code
- ✅ Email OTP verification (valid for 10 minutes)
- 📥 Visitor registration via invitation link
- 📊 Dashboard to view registered visitors and cards
- 🧹 Auto-delete expired events (1 day after event date)
- 📎 Bootstrap 5 UI for a clean, responsive design
- 🔒 Role-based access control

---

## 🏗️ Technologies Used

- Python 3.x
- Flask
- Flask-Mail
- Flask-SQLAlchemy
- SQLite
- WeasyPrint (for PDF generation)
- qrcode (QR code generation)
- Bootstrap 5

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/event-invitation-system.git
cd event-invitation-system

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```
