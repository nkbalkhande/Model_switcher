# auth.py

from flask import Blueprint, request, redirect, render_template, session, flash
from werkzeug.security import check_password_hash
from models import register_user, get_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role", "user")
        try:
            register_user(username, password, role)
            flash("Registered successfully!", "success")
            return redirect("/login")
        except:
            flash("Username already exists!", "danger")
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = get_user(username)
        if user and check_password_hash(user[2], password):
            session["user"] = username
            session["role"] = user[3]
            return redirect("/")
        else:
            flash("Invalid credentials!", "danger")
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect("/login")
