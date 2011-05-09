from django import forms
from models import Submission, License, Revision

class Submission_Common_Form(forms.Form):
    """
    The common parts to all submissions:

        * The submission's title
        * A short summary
    """
    required_css_class = 'scipycentral-form-required'
    error_css_class = 'scipycentral-form-error'
    summary = forms.CharField(max_length=150, widget=forms.Textarea,
                label=Revision._meta.get_field('summary').help_text)
    title = forms.CharField(max_length=255, label=('Please provide a title '
                                                   'for your submission'))

class LinkForm(forms.Form):
    """
    Link submission: only requires a URL
    """
    required_css_class = 'scipycentral-form-required'
    error_css_class = 'scipycentral-form-error'

    parent = Revision._meta.get_field('item_url')
    item_url = forms.URLField(label='Link',
                              max_length=parent.max_length,
                              help_text=parent.help_text)

class SnippetForm(forms.Form):
    """
    Code snippet: requires a box to paste the code in
    """
    required_css_class = 'scipycentral-form-required'
    error_css_class = 'scipycentral-form-error'

    snippet = forms.CharField(label="Copy and paste your code snippet/recipe",
        widget=forms.Textarea(attrs={'class':'scipycentral-code-snippet',
                                      'cols': 80, 'rows': 20}),
        help_text=('This code will be licensed under the <a target="_blank" '
                   'href="/licenses">CC0</a> license, which allows other '
                   'users to freely use it.'))

class PackageForm(forms.Form):
    """
    Code package submission: upload a ZIP file
    """
    package_file = forms.FileField(label='Your code in a single ZIP file',
            help_text=('10 Mb limit. Do not include any files named <tt>'
                       'LICENSE.txt</tt> or <tt>DESCRIPTION.txt</tt> as these '
                       'will be automatically generated from the information '
                       'submitted.'))

class LicenseForm(forms.Form):
    """
    Select a license. User must select a license (empty_label designation)
    """
    sub_license = forms.ModelChoiceField(License.objects.all(),
            empty_label=None,
            label="Select a license for your submission",
            help_text='<a href="/licenses">More on licenses</a>')


#
# Packages
#

#class EditForm(forms.Form):
    #def __init__(self, *a, **kw):
        #files = kw.pop('files', [])
        #forms.Form.__init__(self, *a, **kw)
        #self.set_files(files)

    #def set_files(self, files):
        #if 'files' in self.fields:
            #self.fields['files'].choices = [(x, x) for x in files]

#class PackageForm(EditForm):
    #description = forms.CharField(widget=forms.Textarea())

    #license = forms.ModelChoiceField(License.objects.all(), empty_label=None)
    #author = forms.CharField(max_length=256)
    #url = forms.CharField(required=False)

    #files = forms.MultipleChoiceField(choices=(), required=False)
    #upload_file = forms.FileField(required=False)

    #change_comment = forms.CharField(required=True, widget=forms.Textarea())

##
## Infos
##

#class InfoForm(EditForm):
    #description = forms.CharField(widget=forms.Textarea())

    #license = forms.ModelChoiceField(License.objects.all(), empty_label=None)
    #author = forms.CharField(max_length=256)

    #url = forms.CharField()
    #pypi_name = forms.CharField(max_length=256)

    #change_comment = forms.CharField(required=True, widget=forms.Textarea())

##
## Snippets
##

#class SnippetForm(EditForm):
    #description = forms.CharField(widget=forms.Textarea())
    #snippet = forms.CharField(required=False, widget=forms.Textarea())

    #upload_file = forms.FileField(required=False)
    #change_comment = forms.CharField(required=True, widget=forms.Textarea())
