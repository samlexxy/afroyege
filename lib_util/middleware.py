import threading

from unittest.mock import Mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from rest_framework.request import Request as DRFRequest
from django.http import HttpRequest


_thread_locals = threading.local()

def get_anonymous_user():
    try:
        anonymous_user = _thread_locals.anonymous_user
    except AttributeError:
        anonymous_user = _thread_locals.anonymous_user = get_user_model().objects.get(
            email=settings.ANONYMOUS_USER_EMAIL
        )
        # except InternalError as internal_error:
        #     raise InternalError(
        #         'There is an error in previous sql statement.'
        #         ' Check your database logs.'
        #         ' If this happens locally, maybe you need fab bootstrap?'
        #         ' Original error: %s' % internal_error
        #     )
    return anonymous_user


def get_system_user():
    User = get_user_model()
    return User.objects.get(
        **{User.USERNAME_FIELD: settings.SYSTEM_USER_EMAIL}
    )


def set_current_user(user):
    """Set the given user or user ID as the current user of the local thread."""
    if isinstance(user, int):
        User = get_user_model()
        user = User.objects.get(pk=user)
    _thread_locals.user = user


def get_current_user():
    """Returns the currently set user."""
    user = getattr(_thread_locals, "user", None)
    if user is None:
        return get_anonymous_user()
    return user

def get_current_user_or_none():
    """Similar to get_current_user except that if there is no user set it returns None instead of anonymous user.
    You can use this method if you are interested with the current user but don't want to create anonymous user
    if there is no current user.
    """
    return getattr(_thread_locals, "user", None)



def set_current_request(request: HttpRequest | Mock | DRFRequest | None = None):
    _thread_locals.request = request

    def get_user_from_request(request: HttpRequest | Mock | DRFRequest | None):
        """Returns the request's user, if exist,
        otherwise creates and returns a User with the Anonymous email"""
        user = getattr(request, "user", None)
        if user is not None:
            if user.is_authenticated:
                return user
        return get_anonymous_user()

    if request is None:
        set_current_user(None)
    else:
        set_current_user(get_user_from_request(request))


class ThreadLocalsMiddleware(MiddlewareMixin):
    """Middleware that gets various objects from the
    request object and saves them in thread local storage."""

    def process_request(self, request):
        user = getattr(request, "user", None)
        set_current_request(user)

    def process_response(self, request, response):
        set_current_request(None)
        return response

    def process_exception(self, request, exception):
        set_current_request(None)

