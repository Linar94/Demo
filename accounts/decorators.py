from django.http import HttpResponse

def is_anonymous(f):
    def wrapper(request, **kwargs):
        if request.user.is_anonymous():
            return f(request, **kwargs)
        else:
            return HttpResponse('')
    return wrapper

def is_not_activate(f):
    def wrapper(request, **kwargs):
        if request.user.is_active:
            return f(request, **kwargs)
        else:
            return HttpResponse('12')
    return wrapper