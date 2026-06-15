# Add / Edit Expense Form

A single reusable form template handles both adding and editing an expense.
Flask passes an `expense` object (or `None`) to distinguish the two modes.

## Flask route changes needed (`app.py`)

```python
CATEGORIES = ["Food", "Transport", "Shopping", "Health", "Entertainment", "Bills", "Other"]

@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    if request.method == "GET":
        return render_template("expense_form.html", expense=None, categories=CATEGORIES)

    title    = request.form.get("title", "").strip()
    amount   = request.form.get("amount", "")
    category = request.form.get("category", "")
    date     = request.form.get("date", "")
    notes    = request.form.get("notes", "").strip()

    errors = {}
    if not title:    errors["title"]    = "Title is required."
    if not amount:   errors["amount"]   = "Amount is required."
    if not category: errors["category"] = "Please select a category."
    if not date:     errors["date"]     = "Date is required."
    try:
        amount = float(amount)
        if amount <= 0: errors["amount"] = "Amount must be positive."
    except ValueError:
        errors["amount"] = "Amount must be a number."

    if errors:
        return render_template("expense_form.html", expense=None,
                               categories=CATEGORIES, errors=errors,
                               form=request.form)

    db = get_db()
    db.execute(
        "INSERT INTO expenses (user_id, title, amount, category, date, notes) VALUES (?,?,?,?,?,?)",
        (session["user_id"], title, amount, category, date, notes)
    )
    db.commit()
    db.close()
    flash("Expense added!", "success")
    return redirect(url_for("expenses"))


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))
    db = get_db()
    expense = db.execute(
        "SELECT * FROM expenses WHERE id=? AND user_id=?",
        (id, session["user_id"])
    ).fetchone()
    if not expense:
        db.close()
        return redirect(url_for("expenses"))

    if request.method == "GET":
        db.close()
        return render_template("expense_form.html", expense=expense, categories=CATEGORIES)

    title    = request.form.get("title", "").strip()
    amount   = request.form.get("amount", "")
    category = request.form.get("category", "")
    date     = request.form.get("date", "")
    notes    = request.form.get("notes", "").strip()
    errors = {}
    if not title:    errors["title"]    = "Title is required."
    if not amount:   errors["amount"]   = "Amount is required."
    if not category: errors["category"] = "Please select a category."
    if not date:     errors["date"]     = "Date is required."
    try:
        amount = float(amount)
        if amount <= 0: errors["amount"] = "Amount must be positive."
    except ValueError:
        errors["amount"] = "Amount must be a number."

    if errors:
        db.close()
        return render_template("expense_form.html", expense=expense,
                               categories=CATEGORIES, errors=errors,
                               form=request.form)

    db.execute(
        "UPDATE expenses SET title=?, amount=?, category=?, date=?, notes=? WHERE id=?",
        (title, amount, category, date, notes, id)
    )
    db.commit()
    db.close()
    flash("Expense updated!", "success")
    return redirect(url_for("expenses"))
```

## File: `templates/expense_form.html`

```html
{% extends "base.html" %}
{% block title %}{{ 'Edit' if expense else 'Add' }} Expense — Expense Tracker{% endblock %}
{% block extra_css %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/expense_form.css') }}">
{% endblock %}

{% block content %}
<div class="page-header">
  <h1 class="page-title">{{ 'Edit expense' if expense else 'Add expense' }}</h1>
  <p class="page-subtitle">{{ 'Update the details below.' if expense else 'Fill in the details below.' }}</p>
</div>

<div class="form-card card">
  <form method="POST"
        action="{{ url_for('edit_expense', id=expense.id) if expense else url_for('add_expense') }}">

    <div class="form-row">
      <div class="form-group">
        <label class="form-label" for="title">Title *</label>
        <input type="text" id="title" name="title" class="form-input
               {% if errors and errors.title %}form-input--error{% endif %}"
               value="{{ form.title if form else (expense.title if expense else '') }}"
               placeholder="e.g. Coffee, Rent, Grocery…" required>
        {% if errors and errors.title %}
          <p class="form-error">{{ errors.title }}</p>
        {% endif %}
      </div>

      <div class="form-group">
        <label class="form-label" for="amount">Amount (₹) *</label>
        <input type="number" id="amount" name="amount" class="form-input
               {% if errors and errors.amount %}form-input--error{% endif %}"
               value="{{ form.amount if form else (expense.amount if expense else '') }}"
               step="0.01" min="0.01" placeholder="0.00" required>
        {% if errors and errors.amount %}
          <p class="form-error">{{ errors.amount }}</p>
        {% endif %}
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label class="form-label" for="category">Category *</label>
        <select id="category" name="category" class="form-select
                {% if errors and errors.category %}form-input--error{% endif %}" required>
          <option value="">Select a category</option>
          {% for c in categories %}
            <option value="{{ c }}"
              {% if (form and form.category == c) or (expense and expense.category == c) %}
                selected
              {% endif %}>{{ c }}</option>
          {% endfor %}
        </select>
        {% if errors and errors.category %}
          <p class="form-error">{{ errors.category }}</p>
        {% endif %}
      </div>

      <div class="form-group">
        <label class="form-label" for="date">Date *</label>
        <input type="date" id="date" name="date" class="form-input
               {% if errors and errors.date %}form-input--error{% endif %}"
               value="{{ form.date if form else (expense.date if expense else '') }}" required>
        {% if errors and errors.date %}
          <p class="form-error">{{ errors.date }}</p>
        {% endif %}
      </div>
    </div>

    <div class="form-group">
      <label class="form-label" for="notes">Notes <span class="optional">(optional)</span></label>
      <textarea id="notes" name="notes" class="form-textarea" rows="3"
                placeholder="Any extra details…">{{ form.notes if form else (expense.notes if expense else '') }}</textarea>
    </div>

    <div class="form-actions">
      <a href="{{ url_for('expenses') }}" class="btn btn-secondary">Cancel</a>
      <button type="submit" class="btn btn-primary">
        {{ 'Update expense' if expense else 'Add expense' }}
      </button>
    </div>
  </form>
</div>
{% endblock %}
```

## File: `static/css/expense_form.css`

```css
.form-card { max-width: 640px; }

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}
@media (max-width: 540px) {
  .form-row { grid-template-columns: 1fr; }
}

.form-input--error {
  border-color: var(--color-danger) !important;
}
.form-input--error:focus {
  box-shadow: 0 0 0 3px var(--color-danger-light) !important;
}

.optional {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-normal);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  margin-top: var(--space-6);
  padding-top: var(--space-6);
  border-top: 1px solid var(--color-border);
}
```