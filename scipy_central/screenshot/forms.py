from django import forms

class ScreenshotForm(forms.Form):
    """
    Upload a screenshot image for the submission
    """
    spc_image_upload = forms.ImageField()