from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user

from app.models import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_value = request.form.get("login", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter((User.username == login_value) | (User.email == login_value.lower())).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Вход выполнен", "success")
            return redirect(url_for("main.knowledge"))

        flash("Неверный логин или пароль", "error")

    return render_template("index.html", page_title="Вход", mode="login", show_form=True)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Пользователь с таким именем или почтой уже существует", "error")
            return render_template("index.html", page_title="Регистрация", mode="register", show_form=True)

        user = User(
            username=username,
            first_name=request.form.get("first_name", "").strip(),
            last_name=request.form.get("last_name", "").strip(),
            group_name=request.form.get("group_name", "").strip(),
            email=email,
            is_admin=False
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Регистрация успешна. Теперь войдите.", "success")
        return redirect(url_for("auth.login"))

    return render_template("index.html", page_title="Регистрация", mode="register", show_form=True)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for("main.knowledge"))