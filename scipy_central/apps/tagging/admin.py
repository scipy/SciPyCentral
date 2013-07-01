from django.contrib import admin
from models import Tag

class TagAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'tag_type', 'description', 'id')
    list_display_links = ('slug',)
    list_per_page = 1000
    ordering = ('slug',)

admin.site.register(Tag, TagAdmin)
