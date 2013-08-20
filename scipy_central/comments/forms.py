from django import forms
from django.contrib.comments.forms import CommentForm
from django.utils.translation import ugettext_lazy as _

from scipy_central.rest_comments.views import compile_rest_to_html
from scipy_central.comments.models import SpcComment

class SpcCommentForm(CommentForm):
    # we want only comment field to be shown on the page
    name = forms.CharField(label=_("Name"), max_length=50, widget=forms.HiddenInput())
    email = forms.EmailField(label=_("Email address"), widget=forms.HiddenInput())
    url = forms.URLField(label=("URL"), required=False, widget=forms.HiddenInput())

    def get_comment_model(self):
        return SpcComment

    def get_comment_create_data(self):
        data = super(SpcCommentForm, self).get_comment_create_data()
        rest_comment = compile_rest_to_html(data['comment'])
        data['rest_comment'] = rest_comment
        return data
