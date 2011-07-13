from django.contrib import admin
from models import PageHit

class PageHitAdmin(admin.ModelAdmin):
    list_display = ('datetime', 'ip_address', 'item', 'item_pk', 'ua_string')
    list_per_page = 1000

admin.site.register(PageHit, PageHitAdmin)
