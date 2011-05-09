from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('scipy_central.submission.views',

    # New submission via the web
    url(r'^new$', 'new_web_submission',
                                     name='scipycentral-new-web-submission'),

    # AJAX: get the HTML for the next steps, after picking the submission type
    url(r'^next-steps$', 'next_steps_HTML', name='scipycentral-next-steps'),

    # AJAX: get the HTML for the tagging code
    url(r'^tagging$', 'HTML_for_tagging', name='scipycentral-tagging-code'),
)
