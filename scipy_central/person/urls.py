from django.conf.urls.defaults import patterns, url
from registration.views import register
from forms import SignUpForm

urlpatterns = patterns('scipy_central.person.views',
    # Just override ``registration`` app's URL for registration so that we
    # can provide our own form class. Everything else from that app's default
    # settings are OK for our site.
    url(r'^register/$', register,
                    {'backend': 'registration.backends.default.DefaultBackend',
                     'form_class': SignUpForm},
                    name='registration_register'),

    # The user's profile page
    url(r'^profile/(?P<slug>[-\w]+)?$', 'profile_page',
                                                     name='spc-user-profile'),

    # Edit the user's profile
    url(r'^profile/(?P<slug>[-\w]+)?/edit$', 'profile_page_edit',
                                                name='spc-user-profile-edit'),
)
