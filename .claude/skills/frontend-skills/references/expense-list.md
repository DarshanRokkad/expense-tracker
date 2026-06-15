# Expense List / Table

Full paginated list of all expenses with filter controls (date range, category, search).

## Flask route changes needed (`app.py`)

```python
@app.route("/expenses")
def expenses():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    db = get_db()
    uid = session["user_id"]

    search   = request.args.get("search", "")
    category = request.args.get("category", "")
    date_from = request.args.get("date_from", "")
    date_to   = request.args.get("date_to", "")
    page      = int(request.args.get("page", 1))
    per_page  = 20

    query  = "SELECT * FROM expenses WHERE user_id=?"
    params = [uid]
    if search:
        query += " AND title LIKE ?"; params.append(f"%{search}%")
    if category:
        query += " AND category=?"; params.append(category)
    if date_from:
        query += " AND date>=?"; params.append(date_from)
    if date_to:
        query += " AND date<=?"; params.append(date_to)

    total = db.execute(f"SELECT COUNT(*) FROM ({query})", params).fetchone()[0]
    query += f" ORDER BY date DESC LIMIT {per_page} OFFSET {(page-1)*per_page}"
    rows = db.execute(query, params).fetchall()

    categories = [r["category"] for r in db.execute(
        "SELECT DISTINCT category FROM expenses WHERE user_id=? ORDER BY category", (uid,)
    ).fetchall()]
    db.close()

    return render_template("expenses.html",
        expenses=rows, categories=categories,
        total=total, page=page, per_page=per_page,
        search=search, category=category,
        date_from=date_from, date_to=date_to,
    )
```

## File: `templates/expenses.html`

```html
{% extends "base.html" %}
{% block title %}Expenses — Expense Tracker{% endblock %}
{% block extra_css %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/expenses.css') }}">
{% endblock %}

{% block content %}
<div class="page-header">
  <div class="page-header-row">
    <div>
      <h1 class="page-title">Expenses</h1>
      <p class="page-subtitle">{{ total }} record{{ 's' if total != 1 }}</p>
    </div>
    <a href="{{ url_for('add_expense') }}" class="btn btn-primary">+ Add expense</a>
  </div>
</div>

<!-- Filters -->
<div class="card filters-card">
  <form method="GET" action="{{ url_for('expenses') }}" class="filters-form">
    <input type="text" name="search" value="{{ search }}"
           placeholder="Search title…" class="form-input filter-search">
    <select name="category" class="form-select filter-select">
      <option value="">All categories</option>
      {% for c in categories %}
        <option value="{{ c }}" {% if c == category %}selected{% endif %}>{{ c }}</option>
      {% endfor %}
    </select>
    <input type="date" name="date_from" value="{{ date_from }}" class="form-input filter-date">
    <input type="date" name="date_to"   value="{{ date_to }}"   class="form-input filter-date">
    <button type="submit" class="btn btn-secondary">Filter</button>
    <a href="{{ url_for('expenses') }}" class="btn btn-secondary">Clear</a>
  </form>
</div>

<!-- Table -->
<div class="card">
  {% if expenses %}
  <table class="expense-table">
    <thead>
      <tr>
        <th>Title</th>
        <th>Category</th>
        <th>Date</th>
        <th class="text-right">Amount</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {% for e in expenses %}
      <tr>
        <td>{{ e.title }}</td>
        <td><span class="badge badge-primary">{{ e.category }}</span></td>
        <td class="text-muted">{{ e.date }}</td>
        <td class="text-right font-semibold">₹{{ "%.2f"|format(e.amount) }}</td>
        <td class="actions-cell">
          <a href="{{ url_for('edit_expense', id=e.id) }}" class="btn btn-secondary btn-sm">Edit</a>
          <form method="POST" action="{{ url_for('delete_expense', id=e.id) }}"
                onsubmit="return confirm('Delete this expense?')">
            <button type="submit" class="btn btn-danger btn-sm">Delete</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <!-- Pagination -->
  {% set total_pages = ((total - 1) // per_page + 1) %}
  {% if total_pages > 1 %}
  <div class="pagination">
    {% if page > 1 %}
      <a href="?page={{ page - 1 }}&search={{ search }}&category={{ category }}&date_from={{ date_from }}&date_to={{ date_to }}"
         class="btn btn-secondary btn-sm">← Prev</a>
    {% endif %}
    <span class="pagination-info">Page {{ page }} of {{ total_pages }}</span>
    {% if page < total_pages %}
      <a href="?page={{ page + 1 }}&search={{ search }}&category={{ category }}&date_from={{ date_from }}&date_to={{ date_to }}"
         class="btn btn-secondary btn-sm">Next →</a>
    {% endif %}
  </div>
  {% endif %}

  {% else %}
  <div class="empty-state">
    <div class="empty-state-icon">📭</div>
    <div class="empty-state-title">No expenses found</div>
    <div class="empty-state-desc">Try adjusting your filters or add a new expense.</div>
  </div>
  {% endif %}
</div>
{% endblock %}
```

## File: `static/css/expenses.css`

```css
.page-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.filters-card { margin-bottom: var(--space-4); }
.filters-form {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
}
.filter-search { flex: 1 1 200px; }
.filter-select { flex: 0 1 160px; }
.filter-date   { flex: 0 1 140px; }

.actions-cell {
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding-top: var(--space-4);
  margin-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}
.pagination-info {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}
```