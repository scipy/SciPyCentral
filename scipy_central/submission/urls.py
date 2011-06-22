from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('scipy_central.submission.views',

    # New snippet submission
    url(r'^new-snippet$', 'new_snippet_submission',
                                            name='spc-new-snippet-submission'),

    # Preview snippet submission
    url(r'^new-snippet-preview$', 'preview_snippet_submission',
                                            name='spc-new-snippet-preview'),

    # Submit snippet submission
    url(r'^new-snippet-submit$', 'submit_snippet_submission',
                                            name='spc-new-snippet-submit'),

    # Show an existing submission; some valid examples include:
    # Maximal information:   http://.../23/draw-an-ellipse/revision/4/
    # Typical link:          http://.../23/draw-an-ellipse/
    # Minimal working link:  http://.../23/
    url(r'(?P<snippet_id>\d)$',
        #/(?P<slug>[-\w]*?)/revision/(<?rev_num>[\d].?)$',
        'view_snippet', name='spc-view-a-submission'),

    # AJAX: get suggestions to complete tagging based on a partial string
    # We will accept any input, but the views function will ignore any
    # characters that cannot appear in a slug (e.g. "$", "&", etc).
    url(r'^tag_autocomplete', 'tag_autocomplete', name='spc-tagging-ajax'),  #/(?P<contains_str>.*)$
)
