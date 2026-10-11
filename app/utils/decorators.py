from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required

def admin_required(view_func):
    """Декоратор: доступ только для администраторов"""
    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        if not getattr(current_user, 'is_admin', False):
            flash("Доступ только для администратора", "error")
            return redirect(url_for("main.knowledge")) # Укажем правильный endpoint позже
        return view_func(*args, **kwargs)
    return wrapped