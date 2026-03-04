# use this for modelling some of the existing django fields
from django.db import models

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.deletion import PROTECT


class UpdateUserField(models.ForeignKey):
    def __init__(self, to=None, **kwargs):
        if not hasattr(settings, "ANONYMOUS_USER_EMAIL"):
            raise ImproperlyConfigured("UpdateUserField require `ANONYMOUS_USER_EMAIL` in settings")
        kwargs.pop("on_delete", None)
        super().__init__(settings.AUTH_USER_MODEL, on_delete=PROTECT, **kwargs)

    def get_default(self):
        from lib_util.middleware import get_current_user

        return get_current_user().pk