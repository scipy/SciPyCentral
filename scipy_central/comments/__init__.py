from scipy_central.comments import forms, models

def get_form():
    """
    Custom comments forms
    """
    return forms.SpcCommentForm

def get_model():
    """
    Custom comments model
    """
    return models.SpcComment
