from django import forms

class ScreenshotForm(forms.Form):
    """
    Upload a screenshot for the submission
    """
    label = 'Upload a <b>screenshot</b>, if you have one available'
    help_text = 'JPEG or PNG (will be resized to 128x128)'
    screenshot = forms.ImageField(label=label, help_text=help_text,
                                  required=False)