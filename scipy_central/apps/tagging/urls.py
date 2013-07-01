from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('scipy_central.apps.tagging.views',

    # AJAX tagging suggestions: to complete tagging based on a partial string
    # We will accept any input, but the views function will ignore any
    # characters that cannot appear in a slug (e.g. "$", "&", etc).
    url(r'^autocomplete', 'tag_autocomplete', name='spc-tagging-ajax'),
)
