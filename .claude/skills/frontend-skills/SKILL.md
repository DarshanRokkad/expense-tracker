---
name: expense-tracker-frontend
description: >
  Reusable frontend patterns for the DarshanRokkad/expense-tracker Flask project.
  Use this skill whenever the user wants to build, style, or improve any HTML/CSS/JS
  for the expense tracker — including the dashboard, expense list table, add/edit forms,
  profile page, nav/sidebar, or any new page. Trigger on any request like "build the
  dashboard", "style the expense form", "create the profile page", "add a chart", "make
  the nav", or "add a new template". Also trigger whenever the user mentions a specific
  template file (e.g. dashboard.html, add_expense.html) or asks to match or improve the
  existing look and feel. Do NOT use for backend (Python/Flask) changes unrelated to HTML
  rendering.
---

# Expense Tracker Frontend Skill

A skill for building clean, minimal HTML/CSS/JS pages and components for the
DarshanRokkad/expense-tracker Flask + Jinja2 project.

## Project Overview

- **Stack**: Python Flask, Jinja2 templates, plain CSS (no frameworks), minimal JS
- **Structure**:
  - `templates/` — Jinja2 HTML files rendered by Flask
  - `static/` — CSS, JS, images
  - `app.py` — Flask routes
- **Style**: Clean, minimal. No CSS frameworks. Custom variables. Lots of whitespace.
- **Repo**: https://github.com/DarshanRokkad/expense-tracker

## Design System

Read `references/design-system.md` before writing any CSS or HTML. It defines:
- CSS custom properties (colors, spacing, typography, shadows, border-radius)
- The base layout (sidebar + main content)
- Utility classes used across all pages

## Pages & Components

When building a specific page or component, read the relevant reference file first:

| Task | Reference file |
|------|---------------|
| Nav / Sidebar | `references/nav-sidebar.md` |
| Dashboard with charts | `references/dashboard.md` |
| Expense list/table | `references/expense-list.md` |
| Add / Edit expense form | `references/expense-form.md` |
| Profile page | `references/profile.md` |
| Flash messages / alerts | `references/alerts.md` |

## Core Conventions

1. **Base template**: Every page extends `base.html`. Always use `{% extends "base.html" %}` and fill `{% block content %}`.
2. **Static files**: CSS goes in `static/css/`, JS in `static/js/`. Reference with `{{ url_for('static', filename='...') }}`.
3. **Links**: Use `{{ url_for('route_name') }}` — never hardcode paths.
4. **Forms**: Always include Flask's CSRF-safe pattern: `method="POST"` + route handles POST.
5. **Flash messages**: Use `{% with messages = get_flashed_messages(with_categories=true) %}` pattern.
6. **Charts**: Use Chart.js loaded from CDN (`https://cdn.jsdelivr.net/npm/chart.js`). Pass data from Flask via `{{ data | tojson }}` in a `<script>` block.
7. **Icons**: Use inline SVG or Unicode symbols. No icon libraries.
8. **Responsiveness**: Mobile-first. Sidebar collapses to top nav on small screens.

## Workflow

1. Read `references/design-system.md` first — always.
2. Read the relevant page reference file.
3. Write the HTML template in `templates/`.
4. Write corresponding CSS in `static/css/<page>.css`.
5. Write JS (if needed) in `static/js/<page>.js`.
6. Show the user the files and explain what Flask route changes (if any) are needed.

## File Naming

- Templates: `templates/<page>.html` (e.g. `dashboard.html`, `add_expense.html`)
- CSS: `static/css/<page>.css` (one per page) + `static/css/base.css` (shared)
- JS: `static/js/<page>.js` (only when needed)