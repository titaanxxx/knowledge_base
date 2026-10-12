from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required


def admin_required(view_func):
    """Декоратор: доступ только для администраторов"""

    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        user_is_admin = getattr(current_user, 'is_admin', False)
        print(f"🔍 ПРОВЕРКА ПРАВ: Пользователь '{current_user.username}', is_admin = {user_is_admin}")

        if not user_is_admin:
            print("❌ ДОСТУП ЗАПРЕЩЕН: Срабатывает редирект на главную")
            flash("Доступ только для администратора", "error")
            return redirect(url_for("main.knowledge"))

        print("✅ ДОСТУП РАЗРЕШЕН: Выполняем целевую функцию")
        return view_func(*args, **kwargs)

    return wrapped