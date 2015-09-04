# Setting up the superuser correctly after ``syncdb``. That's because we have
# subclassed the django.contrib.auth.models.User class, but ``syncdb`` doesn't
# create an entry in the ``UserProfile`` database table.

# Code from  Marty Alchin's book: Pro Django, page 82.
from django.db.models import signals

def validate_superuser(app, created_models, verbosity, **kwargs):
    app_label = app.__name__.split('.')[-2]
    #app_name = __name__.split('.')[-2]
    #app_models = [m for m in created_models if m._meta.app_label == app_label]
    #print(app_label, app_name, app_models)

    if app_label == 'auth':
        from django.conf import settings
        from django.core.exceptions import ImproperlyConfigured
        from django.db.models import get_model
        from django.contrib.auth.models import User
        user_class = get_model(*settings.AUTH_PROFILE_MODULE.split('.', 2))
        if not user_class:
            raise ImproperlyConfigured('Could not get custom user model')

        users = User.objects.all()
        if len(users) == 1 and users[0].is_superuser:
            print 'Validating superuser in the subclassed user table'
            user, created = user_class.objects.get_or_create(user=users[0])
            if created:
                user.is_validated = True
                user.save()

    # While we are here (and this isn't user related) check the name of
    # the site. If it is "example.com", change it to "SciPy-Central.org"
    if app_label == 'sites':
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        if site.name == 'example.com':
            site.name = 'SciPy Central'
            site.domain = 'scipy-central.org'
            site.save()



signals.post_syncdb.connect(validate_superuser)
