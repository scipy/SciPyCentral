from django.contrib import admin
from models import Submission, License

class LicenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'sub_type',  'sub_license',
                    'n_downloads', 'n_views', 'n_revisions')

admin.site.register(License, LicenseAdmin)
admin.site.register(Submission, SubmissionAdmin)
