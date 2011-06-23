from django import forms
from models import UserProfile
from django.utils.safestring import mark_safe

class NewUserForm(forms.Form):
    """Used only for form validation, not for HTML."""
    email = forms.EmailField()
    openid = forms.URLField(required=False)
    username = forms.CharField()
    password = forms.PasswordInput()

class Inline_Signin_Create_Form(forms.Form):
    """ To sign in a user, or create a new account.
    Does this inline with the rest of the form elements, so that user doesn't
    have to come back and repeat the task they were starting.
    """
    required_css_class = 'spc-form-required'
    error_css_class = 'spc-form-error'

    email_openid = forms.CharField(label=mark_safe('Your <a href="http://ope'
            'nid.net/get-an-openid/individuals/" target="_blank">OpenID URL'
            '</a> that begins with <tt>http://</tt> or your email address'),
            initial='http://...     or    user@example.com',
            help_text=('<a class="spc-small-uri" target="_blank"'
                'href="http://openid.net/get-an-openid/">Get an OpenID</a>'))

    # Ideally would like to use a template tag for the Reset Password URL
    password = forms.CharField(max_length=255, label=mark_safe((''
                       'Enter a new password (if creating an account), or '
                       'enter your existing SciPy Central password')),
                        help_text=('<a target="_blank" class="spc-small-uri"'
                                   'href="/user/reset-password/">'
                                   'Forgot password?</a>'),
                        widget=forms.PasswordInput(render_value=False))

class LoginForm(forms.Form):
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255,
                               widget=forms.PasswordInput(render_value=False))
