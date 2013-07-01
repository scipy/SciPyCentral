from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('scipy_central.apps.submission.views',

    # SHOW ITEMS in different ways
    # ============================

    # Creating a new item
    url(r'^new/(?P<item_type>[a-zA-Z]+)/$', 'new_or_edit_submission', name='spc-new-submission'),

    url(r'^(?P<what_view>[a-zA-Z]+)/(?P<extra_info>.+)/$', 'show_items',
                                                       name='spc-show-items'),

    # Editing an item (this URL must come before the next URL rule; also see
    # get_items_or_404(...) function in views.py)
    url(r'^(?P<item_id>\d+)/(?P<rev_id>\d+)/edit/$',
                               'edit_submission', name='spc-edit-submission'),

    # Download an item (this URL must come before the next URL rule; also see
    # get_items_or_404(...) function in views.py)
    url(r'^(?P<item_id>\d+)/(?P<rev_id>\d+)/download/$',
                        'download_submission', name='spc-download-submission'),

    url(r'^(?P<item_id>\d+)/(?P<rev_id>\d+)/show/(?P<filename>.*?)$',
                                           'show_file', name='spc-show-file'),


    # View an existing item: all 3 versions of accessing the item are valid
    #
    # Maximum information:   http://..../23/4/draw-an-ellipse/
    # Typical link:          http://..../23/4/  <-- revision 4
    # Minimal working link:  http://..../23/    <-- shows latest revision
    #
    # See unit tests in "tests.py" before making changes here
    url(r'^(?P<item_id>\d+)+(/)?(?P<rev_id>\d+)?(/)?(?P<slug>[-\w]+)?(/)?',
                                           'view_item', name='spc-view-item'),


    # Validating an item
    url(r'^validate/(?P<code>.+)/$', 'validate_submission',
                                                    name='spc-item-validate'),
)
