from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    """Модель админки, отображающая '-пусто' на пустом поле."""

    empty_value_display = '-пусто-'
