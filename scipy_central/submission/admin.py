from django.contrib import admin
from models import License, Submission, Revision, TagCreation, ZipFile

class LicenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('sub_type', 'slug', 'created_by', 'date_created',
                    'num_revisions')
    list_display_links = ('slug',)
    ordering = ['-date_created']

class RevisionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'reputation', 'score', 'created_by', 'date_created',
                    'sub_license', 'item_url', 'rev_id', 'is_displayed')
    list_display_links = ('title',)
    ordering = ['-date_created']

class TagCreationAdmin(admin.ModelAdmin):
    list_display = ('date_created', 'tag', 'created_by', 'revision')

class ZipFileAdmin(admin.ModelAdmin):
    list_display = ('date_added', 'zip_hash', 'raw_zip_file')

admin.site.register(License, LicenseAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Revision, RevisionAdmin)
admin.site.register(TagCreation, TagCreationAdmin)
admin.site.register(ZipFile, ZipFileAdmin)
