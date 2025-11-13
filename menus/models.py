from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import NoReverseMatch, reverse


class Menu(models.Model):
    """Menu is addressed by its slug inside the template tag."""

    title = models.CharField(max_length=150)
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Identifier used in templates, e.g. {% draw_menu 'main-menu' %}",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('title',)
        verbose_name = 'Menu'
        verbose_name_plural = 'Menus'

    def __str__(self) -> str:
        return self.title


class MenuItem(models.Model):
    """Represents a single node in a menu tree."""

    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name='items',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=150)
    named_url = models.CharField(
        max_length=200,
        blank=True,
        help_text='Name of a URL pattern (takes precedence over direct URL).',
    )
    url = models.CharField(
        max_length=255,
        blank=True,
        help_text='Absolute or relative URL when named URL is not used.',
    )
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('menu', 'parent__id', 'position', 'title')
        verbose_name = 'Menu item'
        verbose_name_plural = 'Menu items'
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(named_url__exact='') & ~Q(url__exact=''))
                    | (~Q(named_url__exact='') & Q(url__exact=''))
                ),
                name='menus_menuitem_single_target',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.title} ({self.menu.slug})'

    def clean(self) -> None:
        super().clean()
        if not self.named_url and not self.url:
            raise ValidationError(
                'Either named URL or direct URL must be provided.'
            )
        if self.named_url and self.url:
            raise ValidationError(
                'Provide either a named URL or a direct URL, not both.'
            )
        if self.parent and self.parent.menu_id != self.menu_id:
            raise ValidationError(
                {'parent': 'Parent item must belong to the same menu.'}
            )
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({'parent': "Item cannot be its own parent."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def is_root(self) -> bool:
        return self.parent_id is None

    def get_resolved_url(self) -> str:
        """Return the URL string that should be used for rendering."""
        if self.named_url:
            try:
                return reverse(self.named_url)
            except NoReverseMatch:
                # Fallback to raw value so issues are visible in UI.
                return self.named_url
        return self.url
