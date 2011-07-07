from django import forms
from registration.forms import RegistrationFormUniqueEmail
import re

class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255,
                               widget=forms.PasswordInput(render_value=False))


attrs_dict = {'class': 'required'}
class SignUpForm(RegistrationFormUniqueEmail):
    """
    Same as ``registration``s default form, except we allow spaces in the
    username.
    """
    username = forms.RegexField(regex=re.compile('^[\w @.-]+$', re.UNICODE),
                                max_length=30,
                                widget=forms.TextInput(attrs=attrs_dict),
                                label="Username",
                                error_messages={'invalid': 'This value must '
                                   'contain only letters, numbers, underscores '
                                   'and spaces.'})

