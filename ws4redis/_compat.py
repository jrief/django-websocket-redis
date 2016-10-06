def is_authenticated(request):
    """Wrapper for checking when a request is authenticated. This checks first
    for a valid request and user, then checks to see if `is_authenticated` is
    a callable in order to be compatible with Django 1.10, wherein using a
    callable for `is_authenticated` is deprecated in favor of a property.
    """
    if not request:
        return False
    if not request.user:
        return False
    if callable(request.user.is_authenticated):
        return request.user.is_authenticated()
    return request.user.is_authenticated
