from django import forms

# to identify objects
thumb_choices = (
    ('r', 'revision'),
    ('c', 'comment'),
)

thumb_types = (
    ('up', 'up_vote'),
    ('down', 'down_vote'),
)

class ThumbsForm(forms.Form):
    thumb_for = forms.ChoiceField(choices=thumb_choices)
    thumb_as = forms.ChoiceField(choices=thumb_types)
    object_pk = forms.IntegerField()
