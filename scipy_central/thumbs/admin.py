from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from scipy_central.thumbs.models import Thumbs

class ThumbsAdmin(admin.ModelAdmin):
    field_sets = (
        (None,
            {'fields': ('content_type', 'object_pk')}
        ),
        (_('Content'),
            {'fields': ('person', 'vote', 'is_valid')}
        ),
        (_('Meta'),
            {'fields': ('submit_date', 'ip_address', 'user_agent')}
        ),
    )
    list_display = ('vote', 'is_valid', 'person', 'content_type', 'object_pk', 'ip_address', 'submit_date')
    list_filter = ('submit_date', 'is_valid')
    ordering = ('-submit_date',)
    search_fields = ('person__username', 'person__email', 'ip_address')

    def save_model(self, request, obj, form, change):
        if not obj.is_valid:
            obj.vote = None
        super(ThumbsAdmin, self).save_model(request, obj, form, change)

admin.site.register(Thumbs, ThumbsAdmin)
