from django import forms
from django.forms.forms import BoundField
from django.utils.safestring import mark_safe
from models import License, Revision
from scipy_central.screenshot.forms import ScreenshotForm as ScreenshotForm

required_css_class = 'spc-form-required'
error_css_class = 'spc-form-error'

# From: http://djangosnippets.org/snippets/316/
class HiddenBaseForm(forms.BaseForm):
    def as_hidden(self):
        """
        Returns this form rendered entirely as hidden fields.
        """
        return mark_safe(u'\n'.join(BoundField(self, field, name).as_hidden() \
                                    for name, field in self.fields.items()))
    as_hidden.needs_autoescape = True

class Submission_Form__Common_Parts(HiddenBaseForm, forms.Form):
    """
    The common parts to all submissions:

        * The submission's title
        * A short summary
    """
    title = forms.CharField(max_length=150, \
                            label=Revision._meta.get_field('title').help_text)

    summary = forms.CharField(max_length=255, widget=forms.Textarea,
                label=Revision._meta.get_field('summary').help_text)

    email = forms.EmailField(label=('Your email address'),
                 help_text=('Since you are not <a href="/user/sign-in/">signed'
                            ' in</a> we will send you an email to confirm'
                            'your submission.'),
                             required=True)

class SnippetForm(Submission_Form__Common_Parts, ScreenshotForm):
    """
    Code snippet: requires a box to paste the code in.
    """
    #NOTE: Any additions to this form will require adding the field name in
    # views.py under the ``new_snippet_submission(...)`` function.

    snippet = forms.CharField(label="Copy and paste your code snippet/recipe",
        widget=forms.Textarea(attrs={'class':'spc-code-snippet',
                                      'cols': 80, 'rows': 20}),
        #help_text=('This code will be licensed under the <a target="_blank" '
        #           'href="/licenses">CC0</a> license, which allows other '
        #           'users to freely use it.')
        initial=('# License: Creative Commons Zero - almost public domain - '
                 'http://scpyce.org/cc0'),
        )

    sub_license = forms.ModelChoiceField(License.objects.filter(slug='CC0'),
        empty_label=None,
        label="Select a license for your submission",
        help_text='<a href="/licenses">More on licenses</a>')

    sub_type = forms.CharField(max_length=10, initial='snippet',
                               widget=forms.HiddenInput(), required=False)

    sub_tags = forms.CharField(max_length=50, label='Tag your submission',
                               help_text=('Please provide between 1 and 5 tags'
                                          ' that describe your code (use '
                                          'commas to separate tags)'))

class PackageForm(Submission_Form__Common_Parts, ScreenshotForm):
    """
    Code package submission: upload a ZIP file
    """
    package_file = forms.FileField(label='Your code in a single ZIP file',
            help_text=('10 Mb limit. Do not include any files named <tt>'
                       'LICENSE.txt</tt> or <tt>DESCRIPTION.txt</tt> as these '
                       'will be automatically generated from the information '
                       'submitted.'))
    sub_license = forms.ModelChoiceField(License.objects.all(),
            empty_label=None,
            label="Select a license for your submission",
            help_text='<a href="/licenses">More on licenses</a>')

class LinkForm(Submission_Form__Common_Parts):
    """
    Link submission: only requires a URL
    """
    parent = Revision._meta.get_field('item_url')
    item_url = forms.URLField(label='Link',
                              max_length=parent.max_length,
                              help_text=parent.help_text)

#class LicenseForm(forms.Form):
    #"""
    #Select a license. User must select a license (empty_label designation)
    #"""
    #sub_license = forms.ModelChoiceField(License.objects.all(),
            #empty_label=None,
            #label="Select a license for your submission",
            #help_text='<a href="/licenses">More on licenses</a>')


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
