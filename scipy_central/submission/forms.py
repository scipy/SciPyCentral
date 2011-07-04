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
    The common parts to all submissions.
    """
    # The primary key (used when a form is being edited
    pk = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    title = forms.CharField(max_length=150, \
                            label=Revision._meta.get_field('title').help_text)

    description = forms.CharField(widget=forms.Textarea(attrs={
                                      'class':'spc-code-description',
                                      'cols': 40, 'rows': 5}),
                label=Revision._meta.get_field('description').help_text,
                help_text=('Let the community know what your submission does, '
                           'how it solves the problem, and/or how it works.'))

    # Non-HTML5 browsers will fallback to "text" input widgets; but this really
    # helps for ipads and modern devices that support HTML5.
    html5_email_widget = widget=forms.TextInput()
    html5_email_widget.input_type = 'email'
    email = forms.EmailField(label=('Your <b>email address</b>'),
                 help_text=('Since you are not <a href="/accounts/login/">signed'
                            ' in</a> we will send you an email to confirm '
                            'your submission.'),
                 required=True, widget=html5_email_widget)

    sub_tags = forms.CharField(max_length=50, label=('Provide some '
                                                     '<b>tags</b>'),
                               help_text=('Please provide between 1 and 5 tags'
                                          ' that describe your submission (use'
                                          ' commas to separate tags)'))


class SnippetForm(Submission_Form__Common_Parts, ScreenshotForm):
    """
    Code snippet: requires a box to paste the code in.
    """
    #NOTE: Any additions to this form will require adding the field name in
    # views.py under the ``new_snippet_submission(...)`` function.

    snippet_code = forms.CharField(label='Copy and paste <b>your code</b> '
                                     'snippet/recipe',
        widget=forms.Textarea(attrs={'class':'spc-code-snippet',
                                      'cols': 80, 'rows': 20}),
        help_text=('Please follow <a target="_blank" href="http://www.python.'
                   'org/dev/peps/pep-0008/">PEP 8 guidelines</a><br><ul>'
                   '<li>No more than 80 characters per row</li>'
                   '<li>Please use spaces and not tabs</li>'
                   '<li>Use 4 spaces to indent, (use 2 if you must)</li>'
                   '<li>Spaces around arithmetic operators</li>'
                   '<li>Comments in the code should supplement your summary'
                   '</li></ul>'
                   ),
        initial=('# License: Creative Commons Zero (almost public domain) '
                 'http://scpyce.org/cc0'),
        )

    choices = License.objects.filter(slug='CC0')
    sub_license = forms.ModelChoiceField(choices, empty_label=None,
        widget=forms.Select(attrs={'class':'form-field-auto-width'},
                choices=choices),
        label="Please select a <b>license</b> for your submission",
        help_text='<a href="/licenses">More on licenses</a>')

    sub_type = forms.CharField(max_length=10, initial='snippet',
                               widget=forms.HiddenInput(), required=False)

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

class LinkForm(Submission_Form__Common_Parts, ScreenshotForm):
    """
    Link submission: only requires a URL
    """
    parent = Revision._meta.get_field('item_url')
    # Here's wishing that Django would support this natively ...
    html5_url_widget = widget=forms.TextInput()
    html5_url_widget.input_type = 'url'
    item_url = forms.URLField(label='<b>Link</b> to resource',
                              max_length=parent.max_length,
                              help_text=parent.help_text,
                              widget=html5_url_widget)

    sub_type = forms.CharField(max_length=10, initial='link',
                               widget=forms.HiddenInput(), required=False)

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
