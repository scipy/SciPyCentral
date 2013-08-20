from django.utils.translation import ugettext_lazy as _
from django.contrib.comments.admin import CommentsAdmin
from django.contrib import admin

from scipy_central.comments.models import SpcComment

class SpcCommentAdmin(CommentsAdmin):
    """
    Custom admin interface for comments
    defined on the top of built-in admin interface
    """
    list_display = CommentsAdmin.list_display
    fieldsets = (
        (None,
            {'fields': ('content_type', 'object_pk', 'site')}
        ),
        (_('Content'),
            {'fields': ('user', 'user_name', 'user_email', 'user_url', 'comment', 'rest_comment')}
        ),
        (_('Metadata'),
            {'fields': ('submit_date', 'ip_address', 'is_public', 'is_removed')}
        ),
    )

admin.site.register(SpcComment, SpcCommentAdmin)
