# django imports
from django import forms
from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils.hashcompat import sha_constructor

# scipy central imports
from scipy_central.person.views import create_new_account_internal
from scipy_central.rest_comments.views import compile_rest_to_html
from scipy_central.submission import models

# python imports
import random
import zipfile

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def get_validation_hash(value):
    """
    Create validation hash for submissions to verify
    submissions
    """
    salt = sha_constructor(str(random.random())).hexdigest()[:5]
    slug = slugify(value)
    if isinstance(slug, unicode):
        slug = slug.encode('utf-8')
    return sha_constructor(salt + slug).hexdigest()

class BaseSubmissionForm(forms.ModelForm):
    """
    Base class for forms
    All classes form submissions are recommended to inherit from this
    """
    sub_tags = forms.CharField(max_length=150, label='Provide some tags',
                               widget=forms.TextInput(attrs={'class': 'spc-autocomplete'}),
                               help_text='Please provide between 1 and 5 tags that describe your '
                                         'submission (use commas to separate tags')

    class Meta:
        model = models.Revision

    def __init__(self, request, *args, **kwargs):
        """
        `email` field is not required for authenticated users.
        
        It is not required to mention this field in `fields` attribute in 
        all inherited classes. By default it is included after all elements
        """
        super(BaseSubmissionForm, self).__init__(*args, **kwargs)

        self.request = request
        
        if not self.request.user.is_authenticated():
            self.fields['email'] = forms.EmailField(label='Your <b>email address</b>',
                                                    help_text='Since you are not signed in we will '
                                                              'send you an email to confirm your '
                                                              'submission',
                                                    required=True)

    def save(self, commit=True):
        instance = super(BaseSubmissionForm, self).save(commit=False)

        user, authenticated = self.request.user, True
        if not self.request.user.is_authenticated():
            # returns object if account alreay present
            user = create_new_account_internal(self.cleaned_data['email'])
            authenticated = False
        
        # submission author
        instance.created_by = user

        # is displayed only if authenticated
        instance.is_displayed = authenticated

        # validation hash
        hash_id = ''
        if not authenticated:
            hash_id = get_validation_hash(instance.title)
        instance.validation_hash = hash_id

        # description in HTML
        instance.description_html = compile_rest_to_html(instance.description)

        if commit:
            instance.save()

        return instance


class SnippetForm(BaseSubmissionForm):
    """
    Snippet submission form
    """
    class Meta(BaseSubmissionForm.Meta):
        fields = ('title', 'item_code', 'description', 'sub_tags', 'sub_license')

    def __init__(self, *args, **kwargs):
        super(SnippetForm, self).__init__(*args, **kwargs)
        self.fields['sub_license'].empty_label = None
        self.fields['sub_license'].queryset = models.License.objects.filter(slug='cc0')
        self.fields['item_code'].initial = \
            '# License: Creative Commons Zero (almost public domain) http://scpyce.org/cc0'


class LinkForm(BaseSubmissionForm):
    """"
    Link submission form
    """
    class Meta(BaseSubmissionForm.Meta):
        fields = ('title', 'description', 'item_url', 'sub_tags')


class PackageForm(BaseSubmissionForm):
    """
    Package submission form

    `package_file` field is not present in Model
    """
    package_file = forms.FileField(label='Your submission in a single ZIP file',
                                   help_text=('25 Mb limit. Do not include any files named '
                                              '<tt>LICENSE.txt</tt> or <tt>DESCRIPTION.txt</tt> '
                                              'as these will be automatically generated from '
                                              'the information submitted.'))

    class Meta(BaseSubmissionForm.Meta):
        fields = ('title', 'description', 'package_file', 'sub_tags', 'sub_license')

    def __init__(self, *args, **kwargs):
        super(PackageForm, self).__init__(*args, **kwargs)
        self.fields['sub_license'].empty_label = None
        self.fields['sub_license'].initial = models.License.objects.get(slug='bsd')

    def clean_package_file(self):
        """
        Validate uploaded package file

        `package_file` memory is not freed if validated.
        It has to be done once it is stored.
        """
        package_file = self.cleaned_data['package_file']

        # Validate the size of compressed zip file
        if package_file.size > settings.SPC['library_max_size']:
            package_file.close()
            raise forms.ValidationError('ZIP file too large')

        # Buf to be used if uploaded file is small & in memory
        package_buf = StringIO()

        # If file stored in temporary dir & large size
        if package_file.multiple_chunks():
            file_path = package_file.temporary_file_path()
            if not zipfile.is_zipfile(file_path):
                package_buf.close()
                package_file.close()
                raise forms.ValidationError('Upload a valid ZIP file. It was not valid')
            zip_obj = zipfile.ZipFile(file_path)

        # or file stored in memory & small size
        else: 
            package_buf.write(package_file.read())
            if not zipfile.is_zipfile(package_buf):
                package_buf.close()
                package_file.close()
                raise forms.ValidationError('Upload a valid ZIP file. It was not valid')
            zip_obj = zipfile.ZipFile(package_buf)
            package_file.seek(0)

        package_size = 0 # size of uncompressed ZIP file
        for each_file in zip_obj.infolist():
            # check for malicious unzipping
            # See warning at http://docs.python.org/library/zipfile.html

            # ZipFile object ensures seperators are always '/'
            file_name = each_file.filename.split('/')
            for idx, entry in enumerate(file_name):
                if entry.startswith('..') or (idx == 0 and entry == ''):
                    zip_obj.close()
                    package_buf.close()
                    package_file.close()
                    raise forms.ValidationError('Please upload a valid ZIP file'
                                                'File contains invalid file name %s'
                                                % each_file.filename)

            # check the CRC 
            # implementation taken from zipfile.ZipFile.testzip (Python 2.7.2)
            chunk_size = 2 ** 20
            try:
                f_obj = zip_obj.open(each_file.filename, 'r')
                while f_obj.read(chunk_size): # check CRC-32
                    pass
            except zipfile.BadZipfile:
                zip_obj.close()
                package_buf.close()
                package_file.close()
                raise forms.ValidationError('Upload a valid ZIP file. %s failed '
                                            'CRC-32 checks' % each_file.filename)

            # check size of uncompressed ZIP file
            # Some ZIP files could be highly compressed, when extracted
            # would flood filesystem
            package_size += each_file.file_size
            if package_size > settings.SPC['library_max_size']:
                zip_obj.close()
                package_buf.close()
                package_file.close()
                raise forms.ValidationError('ZIP file too large')

        zip_obj.close()
        package_buf.close()
        
        return self.cleaned_data['package_file']
