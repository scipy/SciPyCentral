from django.conf.urls.defaults import patterns, url, include
from views import SciPyRegistrationBackend

urlpatterns = patterns('scipy_central.person.views',
    # Just override ``registration`` app's URL for registration so that we
    # can provide our own form class. Everything else from that app's default
    # settings are OK for our site.

    # NOTE: the {% url 'registration_register' %} template tag technically
    # never matches with the below url Since the overridden url and built-in url
    # happens to be same, it does not matter and we don't have to care!
    # If we want to change the below url from register/ to something else, 
    # `name` argument has to be changed along with template tags in all templates
    url(r'^register/$', SciPyRegistrationBackend.as_view(), name='registration_register'),

    url(r'^', include('registration.backends.default.urls')),

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
