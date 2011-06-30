# Setting up the superuser correctly after ``syncdb``. That's because we have
# subclassed the django.contrib.auth.models.User class, but ``syncdb`` doesn't
# create an entry in the ``UserProfile`` database table.

# Code from  Marty Alchin's book: Pro Django, page 82.
from django.db.models import signals
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model
from django.contrib.auth.models import User

def user_report(app, created_models, verbosity, **kwargs):
    app_label = app.__name__.split('.')[-2]
    app_name = __name__.split('.')[-2]

    app_models = [m for m in created_models if m._meta.app_label == app_label]

    if app_label == 'auth':

        user_class = get_model(*settings.CUSTOM_USER_MODEL.split('.', 2))
        if not user_class:
            raise ImproperlyConfigured('Could not get custom user model')

        users = User.objects.all()
        if len(users)==1 and users[0].is_superuser:
            print('Creating superuser in the subclassed database table')
            username = users[0].username
            email = users[0].email
            password = users[0].password

            # Delete the existing superuser
            users[0].delete()

            # Recreate them in the subclassed user class
            user = user_class.objects.create_superuser(username, email, None)
            user.password = password
            user.is_validated = True

            user.save()

            # Also add a ``SciPyCentral`` user that will be the owner of some
            # links and snippets that are preloaded. That user's password will
            # be the same as the site's superuser (user.id == 1).
            print('Creating "SciPyCentral" superuser also')
            username = 'SciPyCentral'
            email = settings.DEFAULT_FROM_EMAIL  # admin@scipy-central.org
            password = users[0].password

            # Recreate them in the subclassed user class
            user = user_class.objects.create_superuser(username, email, None)
            user.password = password
            user.is_validated = True

            user.save()


signals.post_syncdb.connect(user_report)
