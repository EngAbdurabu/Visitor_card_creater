from models import *
from flask import redirect, url_for, g, current_app, session
import functools, os


def login_required_event(func):
    @functools.wraps(func)
    def decorator_func(*args, **kwargs):
        if "event_id" not in session:
            return redirect(url_for("auth.login"))

        # تحميل بيانات الحدث
        g.event = EVENT.query.get(session["event_id"])
        if g.event is None:
            session.clear()
            return redirect(url_for("auth.login"))

        return func(*args, **kwargs)

    return decorator_func


def login_required_admin(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.admin is None:
            return redirect(url_for("admin_login"))
        return view(**kwargs)

    return wrapped_view
