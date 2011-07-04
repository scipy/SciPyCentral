from django.contrib import admin
from models import UserProfile, User


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_validated', 'affiliation',
                    'reputation', 'profile')

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.unregister(User)


# 3rd-party ``registration`` app: connect up the signals
import views
from registration.signals import user_registered, user_activated
user_registered.connect(views.create_new_account)
user_activated.connect(views.account_activation)
