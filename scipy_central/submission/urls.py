from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('scipy_central.submission.views',

    # SNIPPETS
    # ========
    # New snippet submission
    url(r'^new-snippet[/]?$', 'new_snippet_submission',
                                            name='spc-new-snippet-submission'),

    # Preview snippet submission
    url(r'^new-snippet-preview$', 'preview_snippet_submission',
                                            name='spc-new-snippet-preview'),

    # Submit snippet submission
    url(r'^new-snippet-submit$', 'submit_snippet_submission',
                                            name='spc-new-snippet-submit'),


    # LINKS
    # ========
    # New link submission
    url(r'^new-link[/]?$', 'new_or_edit_link_submission',
                                            name='spc-new-link-submission'),

    # Preview link submission
    url(r'^new-link-preview$', 'preview_or_submit_link_submission',
                                            name='spc-new-link-preview'),

    # Preview link submission
    url(r'^new-link-submit$', 'preview_or_submit_link_submission',
                                            name='spc-new-link-submit'),

    # View an existing item: all 3 versions of accessing the item are valid
    #
    # Maximum information:   http://..../23/4/draw-an-ellipse/
    # Typical link:          http://..../23/4/  <-- revision 4
    # Minimal working link:  http://..../23/    <-- shows latest revision
    url(r'^(?P<item_id>(\d+)?)(/(?P<rev_num>(\d+)?))?(/(?P<slug>(.+)?))?',
                                           'view_link', name='spc-view-link'),

    # EDITING
    # =======
    url(r'^(?P<item_id>(\d+)?)(/(?P<rev_num>(\d+)?))?(/(?P<slug>(.+)?))?',
        'edit_submission', name='spc-edit-submission'),


    # TAGGING
    # ========

    # AJAX: get suggestions to complete tagging based on a partial string
    # We will accept any input, but the views function will ignore any
    # characters that cannot appear in a slug (e.g. "$", "&", etc).
    url(r'^tag_autocomplete', 'tag_autocomplete', name='spc-tagging-ajax'),  #/(?P<contains_str>.*)$
)
