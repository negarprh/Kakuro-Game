from flask import Blueprint, flash, redirect, render_template, session, url_for


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def welcome():
    if session.get("user_mode") in {"guest", "registered"}:
        return redirect(url_for("game.menu"))
    return render_template("welcome.html")


@main_bp.post("/guest")
def continue_guest():
    session["user_mode"] = "guest"
    session.pop("user_id", None)
    session.pop("current_board", None)
    session.pop("current_solution", None)
    session.pop("difficulty", None)
    flash("Continuing in guest mode.", "info")
    return redirect(url_for("game.menu"))
