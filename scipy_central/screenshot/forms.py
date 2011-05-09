from django import forms

class ScreenshotForm(forms.Form):
    """
    Upload a screenshot for the submission
    """
    screenshot = forms.ImageField(label='Upload a screenshot, if possible',
                                  help_text='1Mb limit; JPEG or PNG',
                                  required=False)