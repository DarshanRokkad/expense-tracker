# Dashboard

The dashboard is the main page after login. It shows:
- Summary stat cards (total this month, biggest category, transaction count)
- A line/bar chart of spending over the last 30 days
- A doughnut chart of spending by category
- A recent transactions mini-list

## Flask route changes needed (`app.py`)

```python
from datetime import datetime, timedelta
import json

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    db = get_db()
    uid = session["user_id"]

    # Summary
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    total_month = db.execute(
        "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND date>=?",
        (uid, month_start)
    ).fetchone()[0]

    # Spending by day (last 30 days)
    days_data = db.execute("""
        SELECT date, SUM(amount) as total
        FROM expenses
        WHERE user_id=? AND date >= date('now','-30 days')
        GROUP BY date ORDER BY date
    """, (uid,)).fetchall()

    # Spending by category
    cat_data = db.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id=? AND date >= date('now','-30 days')
        GROUP BY category ORDER BY total DESC
    """, (uid,)).fetchall()

    # Recent expenses
    recent = db.execute("""
        SELECT id, title, amount, category, date
        FROM expenses WHERE user_id=? ORDER BY date DESC LIMIT 5
    """, (uid,)).fetchall()

    db.close()
    return render_template("dashboard.html",
        total_month=total_month,
        days_labels=json.dumps([r["date"] for r in days_data]),
        days_values=json.dumps([float(r["total"]) for r in days_data]),
        cat_labels=json.dumps([r["category"] for r in cat_data]),
        cat_values=json.dumps([float(r["total"]) for r in cat_data]),
        recent=recent,
    )
```

## File: `templates/dashboard.html`

```html
{% extends "base.html" %}
{% block title %}Dashboard — Expense Tracker{% endblock %}
{% block extra_css %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css') }}">
{% endblock %}

{% block content %}
<div class="page-header">
  <h1 class="page-title">Dashboard</h1>
  <p class="page-subtitle">Here's your spending summary.</p>
</div>

<!-- Stat cards -->
<div class="stat-grid">
  <div class="stat-card">
    <div class="stat-label">Spent this month</div>
    <div class="stat-value">₹{{ "%.2f"|format(total_month) }}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Transactions (30 days)</div>
    <div class="stat-value">{{ recent | length }}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Top category</div>
    <div class="stat-value" id="topCategory">—</div>
  </div>
</div>

<!-- Charts row -->
<div class="charts-row">
  <div class="card chart-card chart-card--wide">
    <h2 class="chart-title">Spending (last 30 days)</h2>
    <canvas id="lineChart"></canvas>
  </div>
  <div class="card chart-card">
    <h2 class="chart-title">By category</h2>
    <canvas id="doughnutChart"></canvas>
  </div>
</div>

<!-- Recent expenses -->
<div class="card">
  <div class="section-header">
    <h2 class="chart-title">Recent transactions</h2>
    <a href="{{ url_for('add_expense') }}" class="btn btn-primary btn-sm">+ Add expense</a>
  </div>
  {% if recent %}
  <table class="expense-table">
    <thead>
      <tr>
        <th>Title</th>
        <th>Category</th>
        <th>Date</th>
        <th class="text-right">Amount</th>
      </tr>
    </thead>
    <tbody>
      {% for e in recent %}
      <tr>
        <td>{{ e.title }}</td>
        <td><span class="badge badge-primary">{{ e.category }}</span></td>
        <td class="text-muted">{{ e.date }}</td>
        <td class="text-right font-semibold">₹{{ "%.2f"|format(e.amount) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty-state">
    <div class="empty-state-icon">📭</div>
    <div class="empty-state-title">No expenses yet</div>
    <div class="empty-state-desc">Add your first expense to see it here.</div>
  </div>
  {% endif %}
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
const daysLabels = {{ days_labels | safe }};
const daysValues = {{ days_values | safe }};
const catLabels  = {{ cat_labels  | safe }};
const catValues  = {{ cat_values  | safe }};

// Line chart
new Chart(document.getElementById('lineChart'), {
  type: 'bar',
  data: {
    labels: daysLabels,
    datasets: [{
      label: 'Amount (₹)',
      data: daysValues,
      backgroundColor: '#eef2ff',
      borderColor: '#4f46e5',
      borderWidth: 2,
      borderRadius: 4,
    }]
  },
  options: {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, grid: { color: '#f3f4f6' } }, x: { grid: { display: false } } }
  }
});

// Doughnut chart
const COLORS = ['#4f46e5','#22c55e','#f59e0b','#ef4444','#06b6d4','#8b5cf6','#ec4899'];
new Chart(document.getElementById('doughnutChart'), {
  type: 'doughnut',
  data: {
    labels: catLabels,
    datasets: [{ data: catValues, backgroundColor: COLORS, borderWidth: 0 }]
  },
  options: {
    responsive: true,
    cutout: '65%',
    plugins: { legend: { position: 'bottom', labels: { padding: 16, font: { size: 12 } } } }
  }
});

// Fill top category
if (catLabels.length) document.getElementById('topCategory').textContent = catLabels[0];
</script>
{% endblock %}
```

## File: `static/css/dashboard.css`

```css
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}
.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5) var(--space-6);
  box-shadow: var(--shadow-sm);
}
.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}
.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
}

.charts-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}
.chart-card { padding: var(--space-5); }
.chart-card--wide {}
.chart-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--space-4);
  color: var(--color-text);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

/* Expense table (shared, also used in expense-list.html) */
.expense-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}
.expense-table th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  color: var(--color-text-muted);
  font-weight: var(--font-weight-medium);
  border-bottom: 1px solid var(--color-border);
}
.expense-table td {
  padding: var(--space-3);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
}
.expense-table tr:last-child td { border-bottom: none; }
.expense-table tr:hover td { background: var(--color-bg); }
.text-right { text-align: right; }
.text-muted  { color: var(--color-text-muted); }
.font-semibold { font-weight: var(--font-weight-semibold); }

@media (max-width: 768px) {
  .charts-row { grid-template-columns: 1fr; }
}
```