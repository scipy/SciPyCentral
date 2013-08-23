from django.db.models import signals
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in

# scipy_central imports
import models, views

# 3rd-party ``registration`` app: connect up the signals
from registration.signals import user_registered, user_activated

class UserProfileInline(admin.StackedInline):
    model = models.UserProfile
    can_delete = False
    verbose_name_plural = 'profile'
    
class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, )

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Hook up the signals here. Doing it in models.py results in circular imports.
user_registered.connect(views.create_new_account)
user_activated.connect(views.account_activation)
user_logged_in.connect(views.user_logged_in)

# Create a ``UserProfile`` for every user
signals.post_save.connect(views.create_new_account, User)
