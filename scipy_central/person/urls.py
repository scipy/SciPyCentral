from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('scipy_central.person.views',
    # This URL is hard coded in scipy_central.submission.forms
    # because I can't get the reverse() function to work as expected.
    #url(r'^sign-in/$', 'login_page', name='spc-login-signin'),
    #url(r'^$', 'login_page'),

    # Sign-out page
    #url(r'^sign-out/$', 'logout_page', name='spc-logout'),

    # Create account page
    #url(r'^create-account$', 'create_new_account', name='spc-create-account'),

    # The user's profile page
    url(r'^profile/(?P<username_slug>[-\w]+)?(/)?$', 'profile_page',
                                                     name='spc-user-profile'),

    # Edit the user's profile
    url(r'^profile/(?P<username_slug>[-\w]+)?/edit$', 'profile_page_edit',
                                                name='spc-user-profile-edit'),

    # There is one place where this URL is hard-coded. See the ``person`` app
    # in the forms.py file.
    #url(r'^reset-password$', 'forgot_account_details',
    #                                               name='spc-reset-by-email'),

    # Validation during new account creation
    #url(r'^validate$', 'precheck_new_user', name='spc-new-valid', ),
)
