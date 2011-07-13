from django.contrib import admin
from models import License, Submission, Revision, TagCreation

class LicenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('sub_type', 'slug', 'created_by', 'date_created',
                    'num_revisions')

class RevisionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'created_by', 'date_created',
                    'sub_license', 'item_url', 'rev_id', 'is_displayed')

class TagCreationAdmin(admin.ModelAdmin):
    list_display = ('date_created', 'tag', 'created_by', 'revision')

admin.site.register(License, LicenseAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Revision, RevisionAdmin)
admin.site.register(TagCreation, TagCreationAdmin)
