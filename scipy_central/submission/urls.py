from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('scipy_central.submission.views',

    # SHOW ITEMS in different ways
    # ============================
    url(r'^show/$', 'show_items', name='spc-show-all'),
    url(r'^show/tag/(?P<tag>.+)/', 'show_items',
                                                 name='spc-show-items-by-tag'),
    url(r'^show/user/(?P<user>[-\w]+)/', 'show_items',
                                                name='spc-show-items-by-user'),

    # Creating a new item
    url(r'^new/$', 'new_or_edit_submission', name='spc-new-submission'),


    # View an existing item: all 3 versions of accessing the item are valid
    #
    # Maximum information:   http://..../23/4/draw-an-ellipse/
    # Typical link:          http://..../23/4/  <-- revision 4
    # Minimal working link:  http://..../23/    <-- shows latest revision
    #
    # See unit tests in "tests.py" before making changes here
    url(r'^(?P<item_id>\d+)+(/)?(?P<rev_id>\d+)?(/)?(?P<slug>[-\w]+)?(/)?',
                                           'view_link', name='spc-view-link'),

    # Editing an item
    url(r'^edit/(?P<item_id>\d+)/$',
                               'edit_submission', name='spc-edit-submission'),

    # Validating an item
    url(r'^validate/(?P<code>.+)/$', 'validate_submission',
                                                    name='spc-item-validate'),


    # AJAX tagging suggestions: to complete tagging based on a partial string
    # We will accept any input, but the views function will ignore any
    # characters that cannot appear in a slug (e.g. "$", "&", etc).
    url(r'^tag_autocomplete', 'tag_autocomplete', name='spc-tagging-ajax'),
)
