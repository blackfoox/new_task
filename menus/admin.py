from django.contrib import admin

from .models import Menu, MenuItem


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ('title', 'parent', 'named_url', 'url', 'position', 'is_active')
    show_change_link = True
    autocomplete_fields = ('parent',)

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_obj = obj
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'parent' and hasattr(self, 'parent_obj') and self.parent_obj:
            formfield.queryset = formfield.queryset.filter(menu=self.parent_obj)
        return formfield


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    inlines = (MenuItemInline,)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'menu', 'parent', 'position', 'is_active')
    autocomplete_fields = ('parent',)
    list_filter = ('menu', 'is_active')
    list_editable = ('position', 'is_active')
    search_fields = ('title', 'named_url', 'url')
    ordering = ('menu', 'parent__id', 'position', 'title')
