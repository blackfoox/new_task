# Django Tree Menu

This project delivers the requested tree menu without any third-party dependencies:

- menu structure is persisted in the database and edited through the stock Django admin;
- `{% draw_menu %}` template tag can be rendered multiple times per page by passing different slugs;
- the active node is inferred from `request.path`; ancestors and the first level of children stay expanded;
- each render hits the database exactly once and the rest of the work happens in memory;
- menu items can target either named URLs or explicit paths.

## Quick start

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata menus/fixtures/sample_menu.json  # optional demo data
python manage.py runserver
```

After loading the fixture the home page shows both `main-menu` and `footer-menu` instances side by side.

## Admin usage

1. `python manage.py createsuperuser`
2. Open `/admin/` and add a `Menu`:
   - `Menu.slug` is the identifier used in `{% draw_menu 'slug' %}`;
   - every `MenuItem` must specify either `named_url` (preferred) or a direct `url`.

## Template tag

```django
{% load menu_tags %}
<nav>
  {% draw_menu 'main-menu' %}
</nav>
```

The inclusion tag renders a `<nav>` block with `menu__*` CSS hooks for custom styling.

## Tests

```bash
.\.venv\Scripts\python manage.py test
```

Tests cover the tree builder, active-path detection, direct URLs, and model validation.
