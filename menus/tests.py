from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Menu, MenuItem
from .services import MenuTreeBuilder


class MenuTreeBuilderTests(TestCase):
    def setUp(self):
        self.menu = Menu.objects.create(title='Main menu', slug='main-menu')
        self.home = MenuItem.objects.create(
            menu=self.menu,
            title='Home',
            named_url='home',
            position=1,
        )
        self.products = MenuItem.objects.create(
            menu=self.menu,
            title='Products',
            named_url='products',
            position=2,
        )
        self.software = MenuItem.objects.create(
            menu=self.menu,
            title='Software',
            named_url='products_software',
            parent=self.products,
            position=1,
        )
        self.hardware = MenuItem.objects.create(
            menu=self.menu,
            title='Hardware',
            named_url='products_hardware',
            parent=self.products,
            position=2,
        )
        self.contacts = MenuItem.objects.create(
            menu=self.menu,
            title='Contacts',
            url='/contacts/',
            position=3,
        )

    def test_builder_uses_single_query(self):
        builder = MenuTreeBuilder('main-menu', '/')
        with self.assertNumQueries(1):
            tree = builder.build()
        self.assertTrue(tree.nodes)

    def test_active_branch_is_marked(self):
        builder = MenuTreeBuilder('main-menu', '/products/software/')
        tree = builder.build()
        products_node = next(node for node in tree.nodes if node.title == 'Products')
        software_node = next(node for node in products_node.children if node.title == 'Software')
        self.assertTrue(products_node.is_ancestor)
        self.assertTrue(software_node.is_active)
        hardware_node = next(node for node in products_node.children if node.title == 'Hardware')
        self.assertFalse(hardware_node.is_active)
        self.assertFalse(hardware_node.is_ancestor)

    def test_direct_urls_supported(self):
        builder = MenuTreeBuilder('main-menu', '/contacts/')
        tree = builder.build()
        contacts_node = next(node for node in tree.nodes if node.title == 'Contacts')
        self.assertTrue(contacts_node.is_active)
        self.assertEqual(contacts_node.url, '/contacts/')

    def test_parent_must_belong_to_same_menu(self):
        other_menu = Menu.objects.create(title='Footer', slug='footer-menu')
        with self.assertRaises(ValidationError):
            MenuItem.objects.create(
                menu=other_menu,
                title='Invalid child',
                parent=self.products,
                named_url='home',
                position=1,
            )
