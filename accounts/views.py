from repositories.models import Repository
from django.db.transaction import commit_on_success
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.generic import View, TemplateView
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormMixin
from django.contrib.auth import (authenticate, login as login_user,logout as logout_user)
from django.shortcuts import render_to_response, redirect, render
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.template import RequestContext
from jira.client import JIRA
from jira.exceptions import JIRAError
from redmine import Redmine, AuthError
from accounts.forms import RegistrationForm
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
import re
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from accounts import signals
from accounts.decorators import is_anonymous
from django.contrib.sites.models import Site
from django.contrib.sites.models import RequestSite
from accounts.models import RegistrationProfile, TaskTr


class BaseActivationView(TemplateView):
    http_method_names = ['get']
    template_name = 'accounts/activation_complete.html'

    @method_decorator(is_anonymous)
    def dispatch(self, request, *args, **kwargs):
        return super(BaseActivationView, self).dispatch(request, **kwargs)

    def get(self, request, *args, **kwargs):
        activated_user = self.activate(request, *args, **kwargs)
        if activated_user:
            signals.user_activated.send(sender=self.__class__,
                                        user=activated_user,
                                        request=request)
            success_url = self.get_success_url(request, activated_user)
            try:
                to, args, kwargs = success_url
                return redirect(reverse(to), *args, **kwargs)
            except ValueError:
                return redirect(success_url)
        return super(BaseActivationView, self).get(request, *args, **kwargs)

    def activate(self, request, activation_key):

        activated_user = RegistrationProfile.objects.activate_user(activation_key)
        if activated_user:
            signals.user_activated.send(sender=self.__class__,
                                        user=activated_user,
                                        request=request)
        return activated_user

    def get_success_url(self, request, activated_user):
        return ('accounts:accounts_activation_complete', (), {})


class Login(View, TemplateResponseMixin):

    @method_decorator(is_anonymous)
    def dispatch(self, request, *args, **kwargs):
        return super(Login, self).dispatch(request, **kwargs)

    def get(self, request, *args, **kwargs):
        return render_to_response('accounts/login.html',
            context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login_user(request, user)
                return redirect(reverse('index'))
            else:
                messages.error(request, ('Your account is disabled.  Make sure you have activated your account.'))
        else:
            messages.error(request, ('Invalid username/password'))
        return render_to_response('accounts/login.html',
            context_instance=RequestContext(request))

@login_required
def logout(request):
    logout_user(request)
    return HttpResponseRedirect(reverse('index'))

def check_password(password):
    p = re.compile('^[a-zA-Z0-9]{8,29}[a-zA-Z0-9]$')
    m = p.match(password)
    if m:
        return True
    else:
        return False

def check_username(username):
    p = re.compile(r'^[\w.@+-]+$')
    m = p.match(username)
    if m:
        return True
    else:
        return False

class Registration(View, TemplateResponseMixin, FormMixin):
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
    success_url = 'accounts:registration_complete'
    form_class = RegistrationForm
    template_name = 'accounts/reg.html'

    @method_decorator(is_anonymous)
    def dispatch(self, request, *args, **kwargs):
        return super(Registration, self).dispatch(request, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {'form': self.get_form(self.get_form_class())})

    def get_success_url(self):
        return 'accounts:registration_complete'

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.get_form_class())
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        return self.get(self.request)

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        conf_password = form.cleaned_data['conf_password']
        email = form.cleaned_data['email']

        if check_username(username)== True:
            if User.objects.filter(username=username):
                return render(self.request, 'accounts/reg.html', {'form': form, 'error': 'This username already exists'})
        else:
            return render(self.request, 'accounts/reg.html', {'form': form, 'error': 'This value may contain only letters, numbers and @/./+/-/_ characters'})
        if User.objects.filter(email=email):
            return render(self.request, 'accounts/reg.html', {'form': form, 'error': 'This email already exists'})
        if check_password(password) == True:
            if (password != conf_password):
                return render(self.request, 'accounts/reg.html', {'form': form, 'error': 'Passwords not matching'})
        else:
            return render(self.request, 'accounts/reg.html', {'form': form, 'error': 'Password length 8-30,includes letters upper and lower case letters, numbers'})

        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(self.request)

        new_user = RegistrationProfile.objects.create_inactive_user(username, email, password, site)

        signals.user_registered.send(sender=self.__class__, user=new_user, request=self.request)

        return redirect(reverse(self.get_success_url()))

@login_required
@require_POST
def _task_tr_account(request):

    if request.is_ajax():
        task_tr_name = request.POST['task_tr']
        username = request.POST['username']
        password = request.POST['password']
        server = request.POST['server']
        proj = request.POST['proj']

        try:
            if task_tr_name == 'redmine':
                try:
                    Redmine(server, username=username, password=password)
                except AuthError:
                    return HttpResponse('ERROR: Redmine error')
            elif task_tr_name == 'jira':
                try:
                    JIRA(basic_auth=(username, password), options={'server': server})
                except JIRAError:
                    return HttpResponse('ERROR: Jira error')
            else:
                return HttpResponse('ERROR: Task tracker name not matched')
            with commit_on_success():

                task_tracker = TaskTr()
                task_tracker.repo = Repository.objects.get(name=proj)
                task_tracker.task_tr_name = task_tr_name
                task_tracker.username = username
                task_tracker.password = password
                task_tracker.server = server
                task_tracker.user = User.objects.get(id=request.user.id)
                task_tracker.save()

            return HttpResponse('SUCCESS: Task tracker successfully added')
        except:
            return HttpResponse('ERROR: Task tracker is not added')
    else:
        return HttpResponse('ERROR: None ajax request')