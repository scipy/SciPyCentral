from django.conf import settings

def global_template_variables(request):
    return {'JQUERY_URL': settings.JQUERY_URL,
             'JQUERYUI_URL': settings.JQUERYUI_URL,
             'JQUERYUI_CSS': settings.JQUERYUI_CSS,
             'ANALYTICS_SNIPPET': settings.ANALYTICS_SNIPPET,
             # Assume the submitting user is not validated, by default
             'validated_user': False,
             'short_URL': settings.SPC['short_URL_root'],
            }