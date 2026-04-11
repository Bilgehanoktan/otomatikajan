# Sovereign Dashboard Architecture: The Triangle of Truth

To ensure the Sovereign AGI Dashboard remains functional and production-ready, any modification to the navigation system must satisfy the **Triangle of Truth**. 

A regression occurs if any vertex of this triangle is broken.

## 1. The Vertices

### Vertex A: navigation (UI Layer)
**Location:** `apps/dashboard/components/sidebar.html`
**Requirement:** Every navigation item must call `showPage('token')` with a unique, lowercase token.
```html
<a href="#" onclick="showPage('ceo')">CEO Engine</a>
```

### Vertex B: container (HTML Layer)
**Location:** `apps/dashboard/index.html`
**Requirement:** There must be a corresponding div with `id="page-{token}"` in the `#content` area.
```html
<div id="page-ceo" class="page"></div>
```

### Vertex C: route (Logic Layer)
**Location:** `apps/dashboard/js/sovereign_core_v121.js`
**Requirement:** The `showPage(name)` function must have a `case '{token}':` in its switch statement to load the feature modules.
```javascript
case 'ceo': loadCEOFindings(); break;
```

## 2. Automated Enforcement
We use the **Dashboard Integrity Guardian** to enforce this triangle.
- **Script:** `tools/maintenance/dashboard_guardian.py`
- **Execution:** This script is automatically called by the central `verify_sovereign_integrity.py` suite.

## 3. Deployment Rules
- **No `__init__.py`**: Static directories under `apps/dashboard/` must never contain Python `__init__.py` files as they are served as raw assets.
- **Lowercase Tokens**: Always use lowercase kebab-case for tokens to avoid Windows/Linux filesystem and URL case-sensitivity issues.
