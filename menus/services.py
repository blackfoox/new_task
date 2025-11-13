from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional
from urllib.parse import urlsplit

from django.db.models import QuerySet

from .models import MenuItem


@dataclass(slots=True)
class MenuNode:
    pk: int
    title: str
    url: str
    position: int
    depth: int = 0
    is_active: bool = False
    is_ancestor: bool = False
    parent: Optional['MenuNode'] = None
    children: List['MenuNode'] = field(default_factory=list)

    @property
    def css_classes(self) -> str:
        classes: list[str] = []
        if self.is_active:
            classes.append('menu-item--active')
        if self.is_ancestor:
            classes.append('menu-item--ancestor')
        if self.is_expanded:
            classes.append('menu-item--expanded')
        return ' '.join(classes)

    @property
    def is_expanded(self) -> bool:
        return self.is_active or self.is_ancestor


@dataclass(slots=True)
class MenuTree:
    menu_title: Optional[str]
    nodes: List[MenuNode]

    def __bool__(self) -> bool:
        return bool(self.nodes)


class MenuTreeBuilder:
    """Builds an in-memory tree in a single DB query."""

    def __init__(self, menu_slug: str, current_path: Optional[str]):
        self.menu_slug = menu_slug
        self.current_path = self._normalize_path(current_path)

    def build(self) -> MenuTree:
        items = list(self._items_queryset())
        menu_title = items[0].menu.title if items else None
        node_map = self._hydrate_nodes(items)
        roots = self._link_nodes(items, node_map)
        self._flag_active_path(node_map.values())
        return MenuTree(menu_title=menu_title, nodes=roots)

    def _items_queryset(self) -> QuerySet[MenuItem]:
        return (
            MenuItem.objects.filter(
                menu__slug=self.menu_slug,
                menu__is_active=True,
                is_active=True,
            )
            .select_related('menu', 'parent')
            .order_by('position', 'pk')
        )

    def _hydrate_nodes(self, items: Iterable[MenuItem]) -> dict[int, MenuNode]:
        node_map: dict[int, MenuNode] = {}
        for item in items:
            node_map[item.pk] = MenuNode(
                pk=item.pk,
                title=item.title,
                url=item.get_resolved_url(),
                position=item.position,
            )
        return node_map

    def _link_nodes(
        self,
        items: List[MenuItem],
        node_map: dict[int, MenuNode],
    ) -> List[MenuNode]:
        roots: list[MenuNode] = []
        for item in items:
            node = node_map[item.pk]
            if item.parent_id and item.parent_id in node_map:
                parent = node_map[item.parent_id]
                node.parent = parent
                node.depth = parent.depth + 1
                parent.children.append(node)
            else:
                roots.append(node)

        for node in node_map.values():
            node.children.sort(
                key=lambda child: (child.position, child.title.lower(), child.pk)
            )
        roots.sort(key=lambda child: (child.position, child.title.lower(), child.pk))
        return roots

    def _flag_active_path(self, nodes: Iterable[MenuNode]) -> None:
        if not self.current_path:
            return
        active_node = next(
            (
                node
                for node in nodes
                if self._normalize_path(node.url) == self.current_path
            ),
            None,
        )
        if not active_node:
            return
        active_node.is_active = True
        parent = active_node.parent
        while parent:
            parent.is_ancestor = True
            parent = parent.parent

    @staticmethod
    def _normalize_path(raw_url: Optional[str]) -> Optional[str]:
        if not raw_url:
            return None
        parsed = urlsplit(raw_url)
        path = parsed.path or '/'
        if not path.startswith('/'):
            path = '/' + path
        normalized = path.rstrip('/') or '/'
        return normalized
