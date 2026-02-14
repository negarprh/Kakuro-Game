from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..services.auth_service import authenticate_user, register_user


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        try:
            user = register_user(username, email, password)
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("signup.html", username=username, email=email)

        session["user_id"] = user.id
        session["user_mode"] = "registered"
        flash("Account created. You are now logged in.", "success")
        return redirect(url_for("game.menu"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "")
        password = request.form.get("password", "")

        user = authenticate_user(identifier, password)
        if user is None:
            flash("Invalid credentials.", "danger")
            return render_template("login.html", identifier=identifier)

        session["user_id"] = user.id
        session["user_mode"] = "registered"
        flash("Logged in successfully.", "success")
        return redirect(url_for("game.menu"))

    return render_template("login.html")


@auth_bp.post("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("main.welcome"))
