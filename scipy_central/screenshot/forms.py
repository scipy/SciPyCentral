from django import forms

class ScreenshotForm(forms.Form):
    """
    Upload a screenshot for the submission
    """
    screenshot = forms.ImageField(label=('Upload a screenshot, if you have ',
                                         'one available'), help_text=('JPEG '
                                         'or PNG (will be resized to 128x128'),
                                  required=False)