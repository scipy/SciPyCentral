from django.conf import settings
from datetime import datetime

def global_template_variables(request):
    return {'JQUERY_URL': settings.JQUERY_URL,
             'JQUERYUI_URL': settings.JQUERYUI_URL,
             'JQUERYUI_CSS': settings.JQUERYUI_CSS,
             'THE_YEAR': str(datetime.now().year),
            }