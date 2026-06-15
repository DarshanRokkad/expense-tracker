import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = "dev-secret-change-in-production"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("landing"))
        return render_template("register.html")

    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required.")
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.")

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return render_template("register.html", error="An account with that email already exists.")
    finally:
        db.close()

    return render_template("register.html", success=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("landing"))
        return render_template("login.html")

    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    db   = get_db()
    user = db.execute(
        "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()
    db.close()

    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"]   = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("dashboard"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/dashboard")
def dashboard():
    return "Dashboard — coming in Step 5"


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "member_since": "2026-01-15",
        "initials": "DU",
    }
    stats = {
        "total_spent": "₹6,110",
        "transaction_count": 8,
        "top_category": "Shopping",
    }
    transactions = [
        {"date": "2026-06-15", "description": "Restaurant lunch",  "category": "Food",          "amount": "₹450"},
        {"date": "2026-06-13", "description": "Miscellaneous",      "category": "Other",         "amount": "₹90"},
        {"date": "2026-06-11", "description": "Clothes",            "category": "Shopping",      "amount": "₹2,200"},
        {"date": "2026-06-09", "description": "Movie tickets",      "category": "Entertainment", "amount": "₹600"},
        {"date": "2026-06-07", "description": "Pharmacy",           "category": "Health",        "amount": "₹800"},
        {"date": "2026-06-05", "description": "Electricity bill",   "category": "Bills",         "amount": "₹1,500"},
        {"date": "2026-06-03", "description": "Auto rickshaw",      "category": "Transport",     "amount": "₹120"},
        {"date": "2026-06-01", "description": "Groceries",          "category": "Food",          "amount": "₹350"},
    ]
    categories = [
        {"name": "Shopping",      "total": "₹2,200", "pct": 36},
        {"name": "Bills",         "total": "₹1,500", "pct": 25},
        {"name": "Health",        "total": "₹800",   "pct": 13},
        {"name": "Food",          "total": "₹800",   "pct": 13},
        {"name": "Entertainment", "total": "₹600",   "pct": 10},
        {"name": "Transport",     "total": "₹120",   "pct": 2},
        {"name": "Other",         "total": "₹90",    "pct": 1},
    ]
    return render_template("profile.html", user=user, stats=stats,
                           transactions=transactions, categories=categories)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
