import math
import sqlite3
from datetime import datetime, date, timedelta
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
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
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
    if not session.get("user_id"):
        return redirect(url_for("login"))

    today       = date.today()
    month_start = today.replace(day=1)

    db = get_db()
    try:
        user_row = db.execute(
            "SELECT id, name FROM users WHERE id = ?",
            (session["user_id"],),
        ).fetchone()

        if user_row is None:
            session.clear()
            return redirect(url_for("login"))

        user = {"name": user_row["name"]}

        # ---- This-month stats ---- #
        month_row = db.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt
            FROM expenses
            WHERE user_id = ? AND date >= ? AND date <= ?
            """,
            (session["user_id"], month_start.isoformat(), today.isoformat()),
        ).fetchone()

        total_spent = month_row["total"]
        stats = {
            "total_spent":       f"₹{total_spent:,.0f}",
            "transaction_count": month_row["cnt"],
            "daily_average":     f"₹{(total_spent / today.day):,.0f}" if total_spent else "₹0",
        }

        # ---- 7-day trend ---- #
        week_start = today - timedelta(days=6)
        day_rows = db.execute(
            """
            SELECT date, COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE user_id = ? AND date >= ? AND date <= ?
            GROUP BY date
            """,
            (session["user_id"], week_start.isoformat(), today.isoformat()),
        ).fetchall()
        totals_by_date = {r["date"]: r["total"] for r in day_rows}

        days = [
            {"label": (week_start + timedelta(days=i)).strftime("%a"),
             "full_date": (week_start + timedelta(days=i)).strftime("%b") + " " + str((week_start + timedelta(days=i)).day),
             "total": totals_by_date.get((week_start + timedelta(days=i)).isoformat(), 0)}
            for i in range(7)
        ]
        max_day_total = max(d["total"] for d in days)
        trend = [
            {**d, "pct": round(d["total"] / max_day_total * 100) if max_day_total else 0,
             "amount_label": f"₹{d['total']:,.0f}"}
            for d in days
        ]

        # ---- Recent transactions ---- #
        rows = db.execute(
            """
            SELECT date, description, category, amount
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
            LIMIT 5
            """,
            (session["user_id"],),
        ).fetchall()
        transactions = [
            {"date": r["date"], "description": r["description"],
             "category": r["category"], "amount": f"₹{r['amount']:,.0f}"}
            for r in rows
        ]
    finally:
        db.close()

    return render_template("dashboard.html", user=user, stats=stats,
                           trend=trend, transactions=transactions)


def _is_valid_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


VALID_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    PAGE_SIZE = 10

    start_date_raw = request.args.get("start_date", "").strip()
    end_date_raw   = request.args.get("end_date", "").strip()

    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1
    page = max(page, 1)

    error = None
    start_date = start_date_raw or None
    end_date   = end_date_raw or None

    if start_date and not _is_valid_date(start_date):
        error = "Invalid start date."
        start_date = end_date = None
    elif end_date and not _is_valid_date(end_date):
        error = "Invalid end date."
        start_date = end_date = None
    elif start_date and end_date and start_date > end_date:
        error = "Start date must be before end date."
        start_date = end_date = None

    filters = {"start_date": start_date_raw, "end_date": end_date_raw}

    date_clauses = []
    date_params  = []
    if start_date:
        date_clauses.append("date >= ?")
        date_params.append(start_date)
    if end_date:
        date_clauses.append("date <= ?")
        date_params.append(end_date)
    date_sql = (" AND " + " AND ".join(date_clauses)) if date_clauses else ""
    query_params = tuple([session["user_id"]] + date_params)

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
            """ + date_sql + """
            GROUP BY category
            ORDER BY total DESC
            """,
            query_params,
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

        total_pages = max(1, (transaction_count + PAGE_SIZE - 1) // PAGE_SIZE)
        page = min(page, total_pages)
        offset = (page - 1) * PAGE_SIZE

        rows = db.execute(
            """
            SELECT id, date, description, category, amount
            FROM expenses
            WHERE user_id = ?
            """ + date_sql + """
            ORDER BY date DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            query_params + (PAGE_SIZE, offset),
        ).fetchall()

        transactions = [
            {
                "id":          r["id"],
                "date":        r["date"],
                "description": r["description"],
                "category":    r["category"],
                "amount":      f"₹{r['amount']:,.0f}",
            }
            for r in rows
        ]

        pagination = {
            "page":        page,
            "total_pages": total_pages,
            "has_prev":    page > 1,
            "has_next":    page < total_pages,
        }
    finally:
        db.close()

    return render_template("profile.html", user=user, stats=stats,
                           transactions=transactions, categories=categories,
                           filters=filters, error=error, pagination=pagination)


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    today = date.today().isoformat()

    if request.method == "GET":
        return render_template("add_expense.html", today=today, categories=VALID_CATEGORIES)

    amount_raw  = request.form.get("amount", "").strip()
    category    = request.form.get("category", "").strip()
    date_raw    = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    error = None
    try:
        amount = float(amount_raw)
    except ValueError:
        amount = None

    if amount is None or not math.isfinite(amount) or amount <= 0:
        error = "Please enter a valid amount greater than 0."
    elif category not in VALID_CATEGORIES:
        error = "Please select a valid category."
    elif not date_raw or not _is_valid_date(date_raw):
        error = "Please enter a valid date."

    if error:
        return render_template(
            "add_expense.html",
            error=error,
            today=today,
            categories=VALID_CATEGORIES,
            form={"amount": amount_raw, "category": category, "date": date_raw, "description": description},
        )

    db = get_db()
    try:
        db.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], amount, category, date_raw, description),
        )
        db.commit()
    finally:
        db.close()

    return redirect(url_for("dashboard"))


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    db = get_db()
    try:
        row = db.execute(
            "SELECT id, amount, category, date, description FROM expenses WHERE id = ? AND user_id = ?",
            (id, session["user_id"]),
        ).fetchone()

        if row is None:
            return redirect(url_for("profile"))

        if request.method == "GET":
            expense = {
                "id": row["id"],
                "amount": f"{row['amount']:.2f}".rstrip("0").rstrip("."),
                "category": row["category"],
                "date": row["date"],
                "description": row["description"],
            }
            return render_template("edit_expense.html", expense=expense, categories=VALID_CATEGORIES)

        amount_raw  = request.form.get("amount", "").strip()
        category    = request.form.get("category", "").strip()
        date_raw    = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        error = None
        try:
            amount = float(amount_raw)
        except ValueError:
            amount = None

        if amount is None or not math.isfinite(amount) or amount <= 0:
            error = "Please enter a valid amount greater than 0."
        elif category not in VALID_CATEGORIES:
            error = "Please select a valid category."
        elif not date_raw or not _is_valid_date(date_raw):
            error = "Please enter a valid date."

        if error:
            expense = {"id": id, "amount": amount_raw, "category": category,
                       "date": date_raw, "description": description}
            return render_template("edit_expense.html", error=error, expense=expense, categories=VALID_CATEGORIES)

        db.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND user_id = ?",
            (amount, category, date_raw, description, id, session["user_id"]),
        )
        db.commit()
    finally:
        db.close()

    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
