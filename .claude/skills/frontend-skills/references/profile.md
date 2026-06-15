# Nav / Sidebar

The sidebar is a vertical navigation panel fixed on the left side on desktop,
collapsing to a top bar with hamburger menu on mobile.

## File: `templates/partials/sidebar.html`

```html
<aside class="sidebar">
  <div class="sidebar-logo">
    <span class="sidebar-logo-icon">💸</span>
    <span class="sidebar-logo-text">ExpenseTracker</span>
  </div>

  <nav class="sidebar-nav">
    <a href="{{ url_for('dashboard') }}"
       class="sidebar-link {% if request.endpoint == 'dashboard' %}active{% endif %}">
      <span class="sidebar-link-icon">📊</span>
      Dashboard
    </a>
    <a href="{{ url_for('add_expense') }}"
       class="sidebar-link {% if request.endpoint == 'add_expense' %}active{% endif %}">
      <span class="sidebar-link-icon">➕</span>
      Add Expense
    </a>
    <a href="{{ url_for('profile') }}"
       class="sidebar-link {% if request.endpoint == 'profile' %}active{% endif %}">
      <span class="sidebar-link-icon">👤</span>
      Profile
    </a>
  </nav>

  <div class="sidebar-footer">
    <div class="sidebar-user">
      <div class="sidebar-user-avatar">{{ session.user_name[0] | upper }}</div>
      <div class="sidebar-user-info">
        <div class="sidebar-user-name">{{ session.user_name }}</div>
        <a href="{{ url_for('logout') }}" class="sidebar-logout">Log out</a>
      </div>
    </div>
  </div>
</aside>

<!-- Mobile top bar -->
<div class="mobile-topbar">
  <button class="mobile-menu-btn" id="menuToggle" aria-label="Open menu">☰</button>
  <span class="sidebar-logo-text">ExpenseTracker</span>
</div>

<!-- Mobile drawer overlay -->
<div class="mobile-overlay" id="mobileOverlay"></div>
```

## File: `static/css/sidebar.css`

```css
/* ---- Sidebar ---- */
.sidebar {
  width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-border);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-lg);
  color: var(--color-text);
}
.sidebar-logo-icon { font-size: 1.5rem; }

.sidebar-nav {
  flex: 1;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: background 0.15s, color 0.15s;
}
.sidebar-link:hover {
  background: var(--color-bg);
  color: var(--color-text);
}
.sidebar-link.active {
  background: var(--color-primary-light);
  color: var(--color-primary);
}
.sidebar-link-icon { font-size: 1rem; width: 1.25rem; text-align: center; }

/* User section at bottom */
.sidebar-footer {
  padding: var(--space-4);
  border-top: 1px solid var(--color-border);
}
.sidebar-user {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.sidebar-user-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-sm);
  flex-shrink: 0;
}
.sidebar-user-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sidebar-logout {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-decoration: none;
}
.sidebar-logout:hover { color: var(--color-danger); }

/* ---- Mobile top bar ---- */
.mobile-topbar {
  display: none;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.mobile-menu-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--color-text);
}

.mobile-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 0.3);
  z-index: 199;
}

@media (max-width: 768px) {
  .mobile-topbar { display: flex; }
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 200;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
  }
  .sidebar.open { transform: translateX(0); }
  .mobile-overlay.open { display: block; }
}
```

## File: `static/js/sidebar.js`

```js
const menuToggle = document.getElementById('menuToggle');
const sidebar    = document.querySelector('.sidebar');
const overlay    = document.getElementById('mobileOverlay');

function openSidebar() {
  sidebar.classList.add('open');
  overlay.classList.add('open');
}
function closeSidebar() {
  sidebar.classList.remove('open');
  overlay.classList.remove('open');
}

menuToggle?.addEventListener('click', openSidebar);
overlay?.addEventListener('click', closeSidebar);
```

## Add to `base.html` `<head>`

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/sidebar.css') }}">
```

## Add to `base.html` before `</body>`

```html
<script src="{{ url_for('static', filename='js/sidebar.js') }}"></script>
```