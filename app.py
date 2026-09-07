import os
from datetime import date

from dotenv import load_dotenv
from flask import (Flask, flash, jsonify, redirect, render_template,
                   request, url_for)

import db
from usda import USDAError, search_foods

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-insecure-key")

MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"]


@app.route("/")
def index():
    log_date = request.args.get("date") or date.today().isoformat()
    entries = db.get_meal_entries(log_date)
    totals = db.get_daily_totals(log_date)

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
def add_entry():
    log_date = request.form.get("log_date") or date.today().isoformat()
    try:
        db.add_meal_entry(
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
def delete_entry(entry_id):
    log_date = request.form.get("log_date") or date.today().isoformat()
    db.delete_meal_entry(entry_id)
    flash("Entry deleted.", "success")
    return redirect(url_for("index", date=log_date))


if __name__ == "__main__":
    app.run(debug=True)