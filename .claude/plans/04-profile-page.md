# Plan: Profile Page (Step 04)

## Context
Replace the `/profile` stub with a fully designed profile page showing hardcoded static data. The goal is to build and validate the complete UI layout — user info card, summary stats, transaction history table, and category breakdown — before real database queries are wired up in Step 5. No POST route, no DB queries, no edit form in this step.

Spec: `.claude/specs/04-profile-page.md`

---

## Files Changed

### 1. `app.py`
Replaced the GET+POST `/profile` handler (which had DB queries and form handling) with a GET-only handler:
- Login guard: `if not session.get("user_id"): return redirect(url_for("login"))`
- Passes four hardcoded context variables to `profile.html`: `user`, `stats`, `transactions`, `categories`
- No DB queries, no `request.form` access

**Hardcoded data:**
- `user` — dict with `name`, `email`, `member_since`, `initials`
- `stats` — dict with `total_spent`, `transaction_count`, `top_category`
- `transactions` — list of 8 dicts: `date`, `description`, `category`, `amount`
- `categories` — list of 7 dicts: `name`, `total`, `pct` (percentage for bar width)

### 2. `templates/profile.html` *(rewritten)*
Four-section layout extending `base.html`. No inline styles except `width: {{ cat.pct }}%` on progress bar fills (structural data-driven width, not a colour value).

Sections:
1. **User info card** (`.user-card`) — `.avatar` circle with initials, name, email, member-since date
2. **Stats row** (`.stats-row`) — three `.stat-card` blocks: total spent, transaction count, top category
3. **Two-column grid** (`.profile-grid`):
   - Left: transaction history table (`.expense-table`) — date, description, category badge, amount
   - Right: category breakdown (`.cat-list`) — name, progress bar, total per category

Category badges use `.badge .badge-<category-lowercase>` classes — no inline colour styles.

### 3. `static/css/style.css`
Added a "Profile page" section with all new classes:
- Layout: `.profile-page`, `.profile-page-title`, `.profile-grid`, `.stats-row`
- Cards: `.user-card`, `.avatar`, `.stat-card`, `.stat-value`, `.stat-label`, `.profile-card`, `.profile-card-header`
- User info: `.user-name`, `.user-email`, `.user-meta`
- Table: `.expense-table` (th, td, `.col-amount`, `.col-date`)
- Category breakdown: `.cat-list`, `.cat-row`, `.cat-row-name`, `.cat-row-total`, `.bar-track`, `.bar-fill`
- Badges: `.badge` base + `.badge-food`, `.badge-transport`, `.badge-bills`, `.badge-health`, `.badge-entertainment`, `.badge-shopping`, `.badge-other`
- Responsive: collapses `profile-grid` and `stats-row` to single column at ≤ 900px

The earlier `.auth-success` rule (added in the previous implementation) remains in the file — it doesn't affect this step.

---

## Reused Patterns
- `session.get("user_id")` inline guard — same as `/register` and `/login` GET handlers
- `.profile-card` visual style mirrors existing `.feature-card` and `.auth-card` conventions
- `.bar-fill` / `.bar-track` mirrors the `.mock-bar-track` / `.mock-bar` pattern from the landing page hero

---

## Verification
1. `source .venv/bin/activate && python app.py`
2. Visit `/profile` without logging in → redirects to `/login`
3. Log in as `demo@spendly.com` / `demo123` → nav shows "Profile" link
4. Visit `/profile` → HTTP 200; page shows user card, 3 stat cards, 8-row transaction table, 7-row category breakdown
5. Inspect HTML → no hex colour values in `profile.html`; category badges use `.badge-*` classes
6. Resize browser to < 900px → grid collapses to single column
