from django.contrib import admin
from models import User, UserProfile
from django.contrib.auth.signals import user_logged_in
from django.db.models import signals

# 3rd-party ``registration`` app: connect up the signals
import views
from registration.signals import user_registered, user_activated

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'is_validated', 'affiliation', 'country',
                    'reputation', 'bio', 'uri', 'openid',
                    'contactable_via_site', 'allow_user_to_email')
    list_display_links = ('user',)
    list_per_page = 1000
    ordering = ('user',)

admin.site.register(UserProfile, UserProfileAdmin)


# Hook up the signals here. Doing it in models.py results in circular imports.
user_registered.connect(views.create_new_account)
user_activated.connect(views.account_activation)
user_logged_in.connect(views.user_logged_in)

# Create a ``UserProfile`` for every user
signals.post_save.connect(views.create_new_account, User)
