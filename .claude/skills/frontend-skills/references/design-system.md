# Design System

This is the single source of truth for all visual decisions in the expense tracker.
Apply these tokens consistently across every page.

---

## CSS Custom Properties

Add these to `static/css/base.css` inside `:root {}`:

```css
:root {
  /* Colors */
  --color-bg:           #f7f8fa;
  --color-surface:      #ffffff;
  --color-border:       #e5e7eb;
  --color-text:         #111827;
  --color-text-muted:   #6b7280;
  --color-primary:      #4f46e5;        /* indigo — action buttons, links */
  --color-primary-light:#eef2ff;        /* indigo tint — hover bg */
  --color-danger:       #ef4444;
  --color-danger-light: #fef2f2;
  --color-success:      #22c55e;
  --color-success-light:#f0fdf4;
  --color-warning:      #f59e0b;
  --color-warning-light:#fffbeb;

  /* Typography */
  --font-family:        'Inter', system-ui, -apple-system, sans-serif;
  --font-size-xs:       0.75rem;   /* 12px */
  --font-size-sm:       0.875rem;  /* 14px */
  --font-size-base:     1rem;      /* 16px */
  --font-size-lg:       1.125rem;  /* 18px */
  --font-size-xl:       1.25rem;   /* 20px */
  --font-size-2xl:      1.5rem;    /* 24px */
  --font-size-3xl:      1.875rem;  /* 30px */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold:   700;
  --line-height:        1.6;

  /* Spacing (multiples of 4px) */
  --space-1:  0.25rem;   /* 4px  */
  --space-2:  0.5rem;    /* 8px  */
  --space-3:  0.75rem;   /* 12px */
  --space-4:  1rem;      /* 16px */
  --space-5:  1.25rem;   /* 20px */
  --space-6:  1.5rem;    /* 24px */
  --space-8:  2rem;      /* 32px */
  --space-10: 2.5rem;    /* 40px */
  --space-12: 3rem;      /* 48px */
  --space-16: 4rem;      /* 64px */

  /* Border radius */
  --radius-sm:   0.25rem;   /* 4px  — inputs, small tags */
  --radius-md:   0.5rem;    /* 8px  — cards, buttons */
  --radius-lg:   0.75rem;   /* 12px — panels */
  --radius-full: 9999px;    /* pills, avatars */

  /* Shadows */
  --shadow-sm:  0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md:  0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -1px rgb(0 0 0 / 0.06);
  --shadow-lg:  0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -2px rgb(0 0 0 / 0.05);

  /* Sidebar */
  --sidebar-width: 240px;
}
```

---

## Base Layout (Sidebar + Main)

The global layout is a two-column grid: fixed sidebar on the left, scrollable main on the right.

```html
<!-- base.html skeleton -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Expense Tracker{% endblock %}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
  {% block extra_css %}{% endblock %}
</head>
<body>
  {% if session.user_id %}
    <div class="app-layout">
      {% include "partials/sidebar.html" %}
      <main class="main-content">
        {% include "partials/flash.html" %}
        {% block content %}{% endblock %}
      </main>
    </div>
  {% else %}
    <div class="auth-layout">
      {% block auth_content %}{% endblock %}
    </div>
  {% endif %}
  {% block extra_js %}{% endblock %}
</body>
</html>
```

```css
/* base.css — layout */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  color: var(--color-text);
  background: var(--color-bg);
  line-height: var(--line-height);
}

/* Authenticated layout */
.app-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
}

.main-content {
  padding: var(--space-8);
  overflow-y: auto;
}

/* Auth layout (login, register) */
.auth-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
}

/* Mobile */
@media (max-width: 768px) {
  .app-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
  .main-content {
    padding: var(--space-4);
  }
}
```

---

## Utility Classes

Include these in `base.css` — use across all templates:

```css
/* Cards */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}

/* Page header */
.page-header {
  margin-bottom: var(--space-8);
}
.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
}
.page-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.15s, box-shadow 0.15s;
}
.btn-primary {
  background: var(--color-primary);
  color: #fff;
}
.btn-primary:hover { background: #4338ca; box-shadow: var(--shadow-md); }
.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text);
  border-color: var(--color-border);
}
.btn-secondary:hover { background: var(--color-bg); }
.btn-danger {
  background: var(--color-danger);
  color: #fff;
}
.btn-danger:hover { background: #dc2626; }
.btn-sm { padding: var(--space-1) var(--space-3); font-size: var(--font-size-xs); }

/* Form elements */
.form-group { margin-bottom: var(--space-5); }
.form-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  margin-bottom: var(--space-2);
}
.form-input, .form-select, .form-textarea {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-base);
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: border-color 0.15s, box-shadow 0.15s;
  font-family: var(--font-family);
}
.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}
.form-error {
  font-size: var(--font-size-xs);
  color: var(--color-danger);
  margin-top: var(--space-1);
}

/* Badge / tag */
.badge {
  display: inline-block;
  padding: 2px var(--space-2);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-full);
}
.badge-primary { background: var(--color-primary-light); color: var(--color-primary); }
.badge-danger  { background: var(--color-danger-light);  color: var(--color-danger);  }
.badge-success { background: var(--color-success-light); color: var(--color-success); }
.badge-warning { background: var(--color-warning-light); color: var(--color-warning); }

/* Empty state */
.empty-state {
  text-align: center;
  padding: var(--space-16) var(--space-8);
  color: var(--color-text-muted);
}
.empty-state-icon { font-size: 2.5rem; margin-bottom: var(--space-4); }
.empty-state-title { font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); }
.empty-state-desc  { font-size: var(--font-size-sm); margin-top: var(--space-2); }
```