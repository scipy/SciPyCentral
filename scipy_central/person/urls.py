from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('scipy_central.person.views',
    # This URL is hard coded in scipy_central.submission.forms
    # because I can't get the reverse() function to work as expected.
    url(r'^sign-in/$', 'login_page', name='spc-login-signin'),
    url(r'^$', 'login_page'),

    # Sign0out page
    url(r'^sign-out/$', 'logout_page', name='spc-logout'),

    # The user's profile page
    url(r'^(\w+)/$', 'profile_page', name='spc-user-profile'),

    # There is one place where this URL is hard-coded. See the ``person`` app
    # in the forms.py file.
    url(r'^reset-password$', 'reset_password', name='spc-reset-email'),

    # Validation during new account creation
    url(r'^validate$', 'precheck_new_user', name='spc-new-valid', ),
)
