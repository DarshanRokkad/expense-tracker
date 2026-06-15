# Flash Messages / Alerts

Flask's `flash()` messages rendered as dismissible banners at the top of the main content area.

## File: `templates/partials/flash.html`

```html
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="flash-container">
      {% for category, message in messages %}
        <div class="flash flash--{{ category }}" role="alert">
          <span>{{ message }}</span>
          <button class="flash-close" aria-label="Dismiss">✕</button>
        </div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}
```

## CSS (add to `base.css`)

```css
.flash-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
}
.flash {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}
.flash--success { background: var(--color-success-light); color: var(--color-success); }
.flash--danger  { background: var(--color-danger-light);  color: var(--color-danger); }
.flash--warning { background: var(--color-warning-light); color: var(--color-warning); }
.flash--info    { background: var(--color-primary-light); color: var(--color-primary); }

.flash-close {
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.6;
  font-size: var(--font-size-xs);
  padding: 0 var(--space-1);
}
.flash-close:hover { opacity: 1; }
```

## JS (add to `base.html` or `base.js`)

```js
document.querySelectorAll('.flash-close').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.closest('.flash').remove();
  });
});
```

## Usage in Flask routes

```python
from flask import flash

flash("Expense added successfully!", "success")
flash("Something went wrong.", "danger")
flash("Please check your input.", "warning")
```