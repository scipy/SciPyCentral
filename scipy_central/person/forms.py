from django import forms
from registration.forms import RegistrationForm
from django.contrib.auth.models import User
import re

class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255,
                               widget=forms.PasswordInput(render_value=False))


attrs_dict = {'class': 'required'}
class SignUpForm(RegistrationForm):
    """
    Same as ``registration``s default form, except we allow spaces in the
    username and for unicode user names.
    """
    username = forms.RegexField(regex=re.compile('^[\w @.-]+$', re.UNICODE),
                                max_length=30,
                                widget=forms.TextInput(attrs=attrs_dict),
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
                raise forms.ValidationError(_("This email address is already "
                                              "in use. Please supply a "
                                              "different email address."))

        return self.cleaned_data['email']

