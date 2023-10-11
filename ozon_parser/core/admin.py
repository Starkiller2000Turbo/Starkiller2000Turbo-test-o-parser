from django.contrib import admin
from django.contrib.auth.models import Group

class BaseAdmin(admin.ModelAdmin):
    """Модель админки, отображающая '-пусто' на пустом поле."""

    empty_value_display = '-пусто-'

admin.site.unregister(Group)