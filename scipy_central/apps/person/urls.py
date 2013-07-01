from django.conf.urls.defaults import patterns, url
from registration.views import register
from forms import SignUpForm
#from models import SciPyRegistrationBackend

urlpatterns = patterns('scipy_central.person.views',
    # Just override ``registration`` app's URL for registration so that we
    # can provide our own form class. Everything else from that app's default
    # settings are OK for our site.
    url(r'^register/$', register,
                    {'backend': 'scipy_central.person.models.SciPyRegistrationBackend',
                     'form_class': SignUpForm},
                    name='registration_register'),

    # The page where the user is redirected to on sign in
    url(r'^profile/$', 'sign_in_landing', name='spc-after-sign-in'),

    # The user's profile page
    url(r'^profile/(?P<slug>[-\w]+)/$', 'profile_page',
                                                     name='spc-user-profile'),

    url(r'^(?P<user_id>\d+)/$', 'profile_page', name='spc-user-profile'),

    # Edit the user's profile
    url(r'^profile/(?P<slug>[-\w]+)/edit/$', 'profile_page_edit',
                                                name='spc-user-profile-edit'),

)
