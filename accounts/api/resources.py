from tastypie.contrib.contenttypes.fields import fields
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie.authentication import *
from tastypie.authorization import *
from accounts.models import *
from django.contrib.auth.models import User
from tastypie.utils import trailing_slash
from django.conf.urls import url
from django.http import HttpResponse
from tastypie.validation import Validation
import json
from tastypie.resources import csrf_exempt
from django.contrib.auth import (authenticate, login as login_user)

class UserResource(ModelResource):

    class Meta:
        queryset = User.objects.all()
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = Authorization()
        resource_name = 'user'
        list_allowed_methods = ['get', 'post']
        excludes = ['password', 'is_staff', 'is_superuser']
        validation = Validation()
        filtering = {
            'username': ALL_WITH_RELATIONS,
        }

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/login%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('_api_login'), name="_api_login"),
        ]

    def _api_login(self, request):

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        data = {}
        status = 200
        if user is not None:
            if user.is_active:
                data['status'] = 'success'
                data['email'] = user.email
                data['api_key'] = user.api_key.key
                data['username'] = username
                login_user(request, user)
            else:
                data['status'] = 'account is disabled'
                status = 403
        else:
            data['status'] = 'access denied'
            status = 401
        return HttpResponse(json.dumps(data), status=status)

    def wrap_view(self, view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            wrapped_view = super(UserResource, self).wrap_view(view)
            return wrapped_view(request, *args, **kwargs)
        return wrapper

class TaskTrResource(ModelResource):

    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = TaskTr.objects.all()
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = Authorization()
        resource_name = 'task_tr'
        list_allowed_methods = ['get', 'post']
        excludes = ('password')
        filtering = {
            'id': ALL_WITH_RELATIONS,
            'username': ALL_WITH_RELATIONS,
            'task_tr_name': ALL_WITH_RELATIONS,
            'server': ALL_WITH_RELATIONS,
        }

class UserProfileResource(ModelResource):

    user = fields.ForeignKey(UserResource, 'user', full=True)

    class Meta:
        queryset = UserProfile.objects.all()
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = Authorization()
        resource_name = 'user prof'
        list_allowed_methods = ['get', 'post']
        filtering = {
            'user': ALL_WITH_RELATIONS,
            'avatar': ALL_WITH_RELATIONS,
        }
