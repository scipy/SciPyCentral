from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('scipy_central.rest_comments.views',

    # AJAX: convert ``text`` field in POST to HTML; to be inserted into DIV
    url(r'', 'rest_to_html_ajax', name='spc-rest-convert'),
)
