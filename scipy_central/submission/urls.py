from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('scipy_central.submission.views',

    # New submission via the web
    url(r'new-snippet', 'new_snippet_submission',
                                            name='spc-new-snippet-submission'),

    ## AJAX: get the HTML for the next steps, after picking the submission type
    #url(r'^next-steps$', 'next_steps_HTML', name='scipycentral-next-steps'),

    # AJAX: get suggestions to complete tagging based on a partial string
    # We will accept any input, but the views function will ignore any
    # characters that cannot appear in a slug (e.g. "$", "&", etc).
    url(r'^tag_autocomplete', 'tag_autocomplete', name='spc-tagging-ajax'),  #/(?P<contains_str>.*)$
)
