from django.contrib import admin
from models import UserProfile, User


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_validated', 'affiliation',
                    'reputation', 'profile')

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.unregister(User)