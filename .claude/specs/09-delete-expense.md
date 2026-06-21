# Spec: Delete Expense

## Overview
Implement the `POST /expenses/<id>/delete` route so a logged-in user can permanently remove one of their own expenses, replacing the current placeholder stub. This is the third and final CRUD step (add → edit → **delete**) and completes the expense management flow started in Steps 7 and 8. Unlike add/edit, delete has no form fields to fill in, so it's a single destructive `POST` action triggered from a "Delete" button next to the existing "Edit" button on `/profile`'s transaction history table, gated behind a client-side confirmation.

## Depends on
- Step 1 (Database setup) — `expenses` table and `get_db()` must be in place.
- Step 3 (Login and Logout) — `session['user_id']` must be set.
- Step 4 (Profile page) — `/profile`'s transaction history table is where the new "Delete" button is added, alongside the "Edit" button from Step 8.
- Step 8 (Edit Expense) — reuses the exact same ownership-check pattern (`WHERE id = ? AND user_id = ?`, silent redirect to `/profile` for a nonexistent or not-owned id) and the `.col-actions` table-cell convention introduced there.

## Routes
- `POST /expenses/<int:id>/delete` — delete that expense if (and only if) it belongs to `session['user_id']`, then redirect to `/profile` — logged-in only. No `GET` handling: a destructive action must never be triggerable by a plain link click, page prefetch, or crawler, so the route only accepts `POST`.

If `id` doesn't exist, or exists but belongs to a different user, redirect to `/profile` without deleting anything and without revealing whether the id exists for someone else — identical behavior to `edit_expense()`'s not-found/not-owned handling.

## Database changes
No database changes. A plain `DELETE FROM expenses WHERE id = ? AND user_id = ?` against the existing table is all that's needed.

## Templates
- **Modify:** `templates/profile.html` — inside the existing `.col-actions` `<td>` (added in Step 8 next to the "Edit" link), add a small inline `<form method="POST" action="{{ url_for('delete_expense', id=txn.id) }}">` containing a single submit button labeled "Delete". The form's `onsubmit` must show a JS `confirm("Delete this expense? This cannot be undone.")` dialog and only submit if the user accepts — this is a UX safety net against accidental clicks, not a security boundary (the server-side ownership check is the real boundary). No new template file is needed — there is no delete confirmation *page*, only a same-page confirmation dialog.

## Files to change
- `app.py` — replace the `delete_expense(id)` stub with a real `POST`-only handler:
  - Auth guard identical to every other protected route.
  - Single `get_db()` connection, `try`/`finally`.
  - `DELETE FROM expenses WHERE id = ? AND user_id = ?` with both `id` and `session['user_id']` as parameters — never trust the URL `id` alone.
  - Redirect to `/profile` whether the delete actually removed a row or not (no distinguishable response for "deleted" vs. "didn't exist" vs. "not yours") — same spirit as `edit_expense()`'s not-found handling.
- `templates/profile.html` — add the inline delete form described above to the `.col-actions` cell.
- `static/css/style.css` — a small additive rule so the Delete button/form sits inline with the Edit link in the same table cell and reads visually as the more destructive of the two actions (e.g. a hover color using the existing `--danger` variable already used by `.auth-error`) — no hex values, no new CSS variables.

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only.
- Parameterised queries only — never use string formatting or f-strings to build SQL.
- Passwords are not touched in this step — no changes to auth logic.
- Use CSS variables — never hardcode hex values; reuse `--danger` (already defined and used by `.auth-error`) for the delete button's hover/accent color rather than inventing a new color.
- All templates extend `base.html` (no change needed here since no new template file is created).
- The route must accept `POST` only — adding `GET` would make the delete action triggerable by a simple link, browser prefetch, or crawler, which is unsafe for a destructive operation.
- The `DELETE` statement's `WHERE` clause must filter on both `id = ?` and `user_id = session['user_id']` — a user must never be able to delete another user's expense by guessing/incrementing the id, even via a crafted `POST`.
- No confirmation *page* — the confirmation is a client-side JS `confirm()` dialog on the existing `/profile` page, consistent with this being a lightweight, same-page action rather than a new route/template.
- On success (or on a no-op for a nonexistent/not-owned id), redirect (don't render) to `/profile` — consistent with how `add_expense()` and `edit_expense()` both redirect rather than render after a state-changing request.

## Definition of done
- [ ] `POST /expenses/<id>/delete` without being logged in redirects to `/login` and deletes nothing.
- [ ] `POST /expenses/<id>/delete` for an id that doesn't exist redirects to `/profile` without crashing and without deleting anything.
- [ ] `POST /expenses/<id>/delete` for an id that belongs to a different user redirects to `/profile` without crashing and without deleting that other user's row.
- [ ] `POST /expenses/<id>/delete` for an id owned by the logged-in user removes exactly that one row from `expenses` and redirects to `/profile`.
- [ ] The deleted expense no longer appears on `/profile` or `/dashboard` immediately after redirect.
- [ ] Deleting one expense never affects any other row — neither another expense of the same user nor any row belonging to a different user.
- [ ] A `GET` request to `/expenses/<id>/delete` does not delete anything (the route only registers `POST`, so Flask itself rejects a `GET` with `405 Method Not Allowed`).
- [ ] `/profile`'s transaction history table shows a working "Delete" button on every row, next to "Edit", that prompts a confirmation dialog before submitting.
- [ ] The app starts without errors after the changes.
- [ ] No hex colour values appear in the modified parts of `profile.html` or any new CSS — only CSS variables.
