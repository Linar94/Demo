from django.conf.urls import patterns, include, url
from accounts.decorators import is_anonymous, is_not_activate
from accounts.views import Login, Registration, BaseActivationView
from django.views.generic.base import TemplateView
from tastypie.api import Api
from accounts.api.resources import *

urlpatterns = patterns('accounts.views',
    url(r'^login/$', is_anonymous(Login.as_view()), name='login'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^activate/(?P<activation_key>\w+)/$', is_anonymous(BaseActivationView.as_view()), name='registration_activate'),
    url(r'^activate/complete/$', TemplateView.as_view(template_name='accounts/activation_complete.html'),
                           name='accounts_activation_complete'),
    url(r'^registration/$', is_anonymous(Registration.as_view()), name='registration'),
    url(r'^register/complete/$', TemplateView.as_view(template_name='accounts/registration_complete.html'),
                                                                                        name='registration_complete'),
    url(r'^task tr/save/$', '_task_tr_account', name='task_tr'),
)

v1_api = Api(api_name='v1')
v1_api.register(TaskTrResource())
v1_api.register(UserResource())
v1_api.register(UserProfileResource())


urlpatterns += patterns('',
    (r'^api/', include(v1_api.urls)),
)