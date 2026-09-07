import os
from datetime import date
from dotenv import load_dotenv
from flask import (Flask, flash, jsonify, redirect, render_template,
request, url_for)
import db
from usda import USDAError, search_foods
from functools import wraps
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-insecure-key")
db.reset_db()

MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]

def login_required(view):
    """Redirect anonymous users to the login page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user_id():
    return session["user_id"]


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3:
            flash("Username needs at least 3 characters.", "error")
        elif len(password) < 8:
            flash("Password needs at least 8 characters.", "error")
        elif db.get_user_by_username(username):
            flash("That username is taken.", "error")
        else:
            user_id = db.create_user(username, generate_password_hash(password))
            session["user_id"] = user_id
            session["username"] = username
            return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = db.get_user_by_username(username)

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))

        flash("Incorrect username or password.", "error")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    log_date = request.args.get("date") or date.today().isoformat()
    entries = db.get_meal_entries(current_user_id(), log_date)
    totals = db.get_daily_totals(current_user_id(), log_date)

    entries_by_meal = {meal: [] for meal in MEAL_TYPES}
    for entry in entries:
        entries_by_meal[entry["meal_type"]].append(entry)

    return render_template(
        "index.html",
        log_date=log_date,
        entries_by_meal=entries_by_meal,
        totals=totals,
        meal_types=MEAL_TYPES,
    )


@app.route("/api/search")
@login_required
def api_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"foods": []})
    try:
        foods = search_foods(query, page_size=8)
    except USDAError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify({"foods": foods})


@app.route("/add", methods=["POST"])
@login_required
def add_entry():
    log_date = request.form.get("log_date") or date.today().isoformat()
    try:
        db.add_meal_entry(
            current_user_id()
            log_date=log_date,
            meal_type=request.form["meal_type"],
            fdc_id=request.form.get("fdc_id") or None,
            description=request.form["description"],
            quantity_g=float(request.form["quantity_g"]),
            calories_per_100g=float(request.form["calories_per_100g"]),
            protein_per_100g=float(request.form["protein_per_100g"]),
            carbs_per_100g=float(request.form["carbs_per_100g"]),
            fat_per_100g=float(request.form["fat_per_100g"]),
        )
        flash(f"Logged {request.form['description']}.", "success")
    except (KeyError, ValueError):
        flash("That entry was missing something. Pick a food and enter grams.", "error")

    return redirect(url_for("index", date=log_date))


@app.route("/delete/<int:entry_id>", methods=["POST"])
@login_required
def delete_entry(entry_id):
    log_date = request.form.get("log_date") or date.today().isoformat()
    db.delete_meal_entry(current_user_id(), entry_id)
    flash("Entry deleted.", "success")
    return redirect(url_for("index", date=log_date))

@app.route("/summary")
@login_required
def summary():
    days = request.args.get("days", 7, type=int)
    days = max(1, min(days, 30))
    summaries = db.get_daily_summaries(current_user_id(), days)

    if summaries:
        avg = {
            key: sum(row[key] for row in summaries) / len(summaries)
            for key in ("calories", "protein", "carbs", "fat")
        }
    else:
        avg = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}

    return render_template("summary.html", summaries=summaries, avg=avg, days=days)

if __name__ == "__main__":
    app.run(debug=True)