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

    db = get_db()
    try:
        user_row = db.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (session["user_id"],),
        ).fetchone()

        if user_row is None:
            session.clear()
            return redirect(url_for("login"))

        words    = user_row["name"].split()
        initials = (words[0][0] + (words[1][0] if len(words) > 1 else "")).upper()
        user = {
            "name":         user_row["name"],
            "email":        user_row["email"],
            "member_since": user_row["created_at"][:10],
            "initials":     initials,
        }

        agg = db.execute(
            """
            SELECT
                COALESCE(SUM(amount), 0)  AS total,
                COUNT(*)                  AS cnt,
                category
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY total DESC
            """,
            (session["user_id"],),
        ).fetchall()

        grand_total       = sum(r["total"] for r in agg)
        transaction_count = sum(r["cnt"]   for r in agg)
        top_category      = agg[0]["category"] if agg else "—"
        stats = {
            "total_spent":       f"₹{grand_total:,.0f}",
            "transaction_count": transaction_count,
            "top_category":      top_category,
        }

        categories = [
            {
                "name":  r["category"],
                "total": f"₹{r['total']:,.0f}",
                "pct":   round(r["total"] / grand_total * 100) if grand_total else 0,
            }
            for r in agg
        ]

        rows = db.execute(
            """
            SELECT date, description, category, amount
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
            LIMIT 10
            """,
            (session["user_id"],),
        ).fetchall()

        transactions = [
            {
                "date":        r["date"],
                "description": r["description"],
                "category":    r["category"],
                "amount":      f"₹{r['amount']:,.0f}",
            }
            for r in rows
        ]
    finally:
        db.close()

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
