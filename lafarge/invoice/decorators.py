from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def user_is_lafarge_or_superuser(function):
    def wrap(request, *args, **kwargs):
        if request.user.is_superuser or request.user.username == 'lafarge':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap