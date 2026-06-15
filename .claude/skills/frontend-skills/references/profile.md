# Profile Page

Shows user info (name, email) with the ability to update their name and/or password.

## Flask route changes needed (`app.py`)

```python
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    db = get_db()
    uid = session["user_id"]
    user = db.execute("SELECT id, name, email FROM users WHERE id=?", (uid,)).fetchone()

    if request.method == "GET":
        db.close()
        return render_template("profile.html", user=user)

    action = request.form.get("action")

    if action == "update_name":
        name = request.form.get("name", "").strip()
        if not name:
            db.close()
            return render_template("profile.html", user=user,
                                   name_error="Name cannot be empty.")
        db.execute("UPDATE users SET name=? WHERE id=?", (name, uid))
        db.commit()
        session["user_name"] = name
        flash("Name updated!", "success")

    elif action == "update_password":
        current = request.form.get("current_password", "")
        new_pw  = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        if not check_password_hash(user["password_hash"], current):
            db.close()
            return render_template("profile.html", user=user,
                                   pw_error="Current password is incorrect.")
        if len(new_pw) < 8:
            db.close()
            return render_template("profile.html", user=user,
                                   pw_error="New password must be at least 8 characters.")
        if new_pw != confirm:
            db.close()
            return render_template("profile.html", user=user,
                                   pw_error="Passwords do not match.")
        db.execute("UPDATE users SET password_hash=? WHERE id=?",
                   (generate_password_hash(new_pw), uid))
        db.commit()
        flash("Password updated!", "success")

    db.close()
    return redirect(url_for("profile"))
```

## File: `templates/profile.html`

```html
{% extends "base.html" %}
{% block title %}Profile — Expense Tracker{% endblock %}
{% block extra_css %}
  <link rel="stylesheet" href="{{ url_for('static', filename='css/profile.css') }}">
{% endblock %}

{% block content %}
<div class="page-header">
  <h1 class="page-title">Profile</h1>
  <p class="page-subtitle">Manage your account details.</p>
</div>

<!-- Avatar + summary -->
<div class="profile-hero card">
  <div class="profile-avatar">{{ user.name[0] | upper }}</div>
  <div class="profile-hero-info">
    <div class="profile-name">{{ user.name }}</div>
    <div class="profile-email">{{ user.email }}</div>
  </div>
</div>

<!-- Update name -->
<div class="card">
  <h2 class="section-title">Display name</h2>
  <form method="POST" action="{{ url_for('profile') }}">
    <input type="hidden" name="action" value="update_name">
    <div class="form-group">
      <label class="form-label" for="name">Name</label>
      <input type="text" id="name" name="name" class="form-input
             {% if name_error %}form-input--error{% endif %}"
             value="{{ user.name }}" required>
      {% if name_error %}<p class="form-error">{{ name_error }}</p>{% endif %}
    </div>
    <button type="submit" class="btn btn-primary">Save name</button>
  </form>
</div>

<!-- Update password -->
<div class="card">
  <h2 class="section-title">Change password</h2>
  <form method="POST" action="{{ url_for('profile') }}" class="password-form">
    <input type="hidden" name="action" value="update_password">
    {% if pw_error %}
      <div class="alert alert-danger">{{ pw_error }}</div>
    {% endif %}
    <div class="form-group">
      <label class="form-label" for="current_password">Current password</label>
      <input type="password" id="current_password" name="current_password"
             class="form-input" required>
    </div>
    <div class="form-group">
      <label class="form-label" for="new_password">New password</label>
      <input type="password" id="new_password" name="new_password"
             class="form-input" minlength="8" required>
    </div>
    <div class="form-group">
      <label class="form-label" for="confirm_password">Confirm new password</label>
      <input type="password" id="confirm_password" name="confirm_password"
             class="form-input" required>
    </div>
    <button type="submit" class="btn btn-primary">Update password</button>
  </form>
</div>
{% endblock %}
```

## File: `static/css/profile.css`

```css
.profile-hero {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}
.profile-avatar {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  flex-shrink: 0;
}
.profile-name {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
}
.profile-email {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
}

/* Stack cards vertically with consistent spacing */
.card + .card { margin-top: var(--space-6); }

.section-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.password-form { max-width: 400px; }

/* Alert box (inline, not flash) */
.alert {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  margin-bottom: var(--space-4);
}
.alert-danger  { background: var(--color-danger-light);  color: var(--color-danger); }
.alert-success { background: var(--color-success-light); color: var(--color-success); }

/* Reuse error class from design system */
.form-input--error { border-color: var(--color-danger) !important; }
```