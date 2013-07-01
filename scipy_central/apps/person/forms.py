from django import forms
from registration.forms import RegistrationForm
from django.contrib.auth.models import User
import re
from models import UserProfile, Country
from scipy_central.apps.utils import rest_help_extra


rest_help = ('Tell the community a bit more about yourself. ') + rest_help_extra

class ProfileEditForm(forms.Form):
    """
    User wants to edit their profile.
    """
    affiliation = forms.CharField(max_length=150, required=False,
                label=UserProfile._meta.get_field('affiliation').help_text)

    choices = Country.objects.all().order_by('name')
    # Country: where the user is based
    country = forms.ModelChoiceField(choices, empty_label='------',
        widget=forms.Select(attrs={'class':'form-field-auto-width'},
                choices=choices),
        required=False,
        label=UserProfile._meta.get_field('country').help_text,
        help_text='<a href="/licenses">More on licenses</a>')

    # profile: a one-line profile about yourself
    bio = forms.CharField(label=UserProfile._meta.get_field('bio').help_text,
                    widget=forms.Textarea(attrs={'class':'spc-user-profile',
                   'cols': 30, 'rows': 20}), help_text=rest_help,
                    required=False)

    # A user-provided URL to their own site or affiliated company
    uri = forms.URLField(label=UserProfile._meta.get_field('uri').help_text,
                         required=False,)

    # List of interests
    interests = forms.CharField(max_length=250, required=False,
                label=('List of <b>your interests</b>:'),
                widget=forms.TextInput(attrs={'class':'spc-autocomplete'}),
                help_text=('Please provide between 1 and 5 tags that '
                           'describe your interests (use commas to separate)'))


    # Non-HTML5 browsers will fallback to "text" input widgets; but this really
    # helps for ipads and modern devices that support HTML5.
    html5_email_widget = forms.TextInput()
    html5_email_widget.input_type = 'email'
    email = forms.EmailField(label=('Your <b>email address &nbsp;&nbsp;*</b>'),
                 help_text=('Your email address will never be shown'),
                 widget=html5_email_widget)



class SignUpForm(RegistrationForm):
    """
    Same as ``registration``s default form, except we allow spaces in the
    username and for unicode user names.
    """
    username = forms.RegexField(regex=re.compile('^[\w @.-]+$', re.UNICODE),
                                max_length=30,
                                widget=forms.TextInput(attrs=
                                    {'class': 'required',
                                     'placeholder': 'e.g. "Mary Appleseed"'}),
                                label="Username",
                                error_messages={'invalid': 'This value must '
                                   'contain only letters, numbers, underscores '
                                   'and spaces.'})

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the site, but
        allow for the case when the email has been "registered" while creating
        a new submission
        """
        basic = User.objects.filter(email__iexact=self.cleaned_data['email'])
        if basic:

            # Not so fast; may be the user has an unconfirmed submission?
            if basic[0].profile.is_validated and basic[0].is_active:
                raise forms.ValidationError(("This email address is already "
                                              "in use. Please supply a "
                                              "different email address."))

        return self.cleaned_data['email']
