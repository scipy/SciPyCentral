from django.conf.urls.defaults import url, patterns

from scipy_central.submission.views import create


urlpatterns = patterns('scipy_central.submission.views',

    # SHOW ITEMS in different ways
    # ============================

    # Creating a new item
    url(r'^(?P<item_type>[a-zA-Z]+)/new/$', create.NewSubmission.as_view(), name='spc-new-submission'),

    url(r'^(?P<what_view>[a-zA-Z]+)/(?P<extra_info>.+)/$', 'show.show_items',
                                                       name='spc-show-items'),

    # Editing an item (this URL must come before the next URL rule
    url(r'^(?P<item_id>\d+)/(?P<rev_id>\d+)/edit/$', create.EditSubmission.as_view(), name='spc-edit-submission'),

    # Download an item (this URL must come before the next URL rule; also see
    # get_items_or_404(...) function in views.show.py)
    url(r'^(?P<item_id>\d+)/(?P<rev_id>\d+)/download/$',
                        'show.download_submission', name='spc-download-submission'),

    # View an existing item: all 3 versions of accessing the item are valid
    #
    # Maximum information:   http://..../23/4/draw-an-ellipse/
    # Typical link:          http://..../23/4/  <-- revision 4
    # Minimal working link:  http://..../23/    <-- shows latest revision
    #
    # See unit tests in "tests.py" before making changes here
    url(r'^(?P<item_id>\d+)+(/)?(?P<rev_id>\d+)?(/)?(?P<slug>[-\w]+)?(/)?',
                                           'show.view_item', name='spc-view-item'),


    # Validating an item
    url(r'^validate/(?P<code>.+)/$', 'show.validate_submission',
                                                    name='spc-item-validate'),
)
