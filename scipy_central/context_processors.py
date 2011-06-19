from django.conf import settings

def global_template_variables(request):
    return {'JQUERY_URL': settings.JQUERY_URL,
             'JQUERYUI_URL': settings.JQUERYUI_URL,
             'JQUERYUI_CSS': settings.JQUERYUI_CSS,
            }