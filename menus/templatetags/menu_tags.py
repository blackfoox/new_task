from __future__ import annotations

from django import template

from menus.services import MenuTreeBuilder

register = template.Library()


@register.inclusion_tag('menus/menu.html', takes_context=True)
def draw_menu(context, menu_slug: str):
    request = context.get('request')
    current_path = getattr(request, 'path', None)
    tree = MenuTreeBuilder(menu_slug=menu_slug, current_path=current_path).build()
    human_title = tree.menu_title or menu_slug.replace('-', ' ').replace('_', ' ').title()
    return {
        'menu_slug': menu_slug,
        'menu_title': human_title,
        'nodes': tree.nodes,
    }
