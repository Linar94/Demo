from django.db import models
import datetime
import random
import hashlib
import re
from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from repositories.models import Repository

tasktr = (('jira', 'jira'), ('redmine', 'redmine'))

class TaskTr(models.Model):
    user = models.ForeignKey(User, 'id')
    repo = models.ForeignKey(Repository)
    task_tr_name = models.CharField(choices=tasktr, max_length=7)
    username = models.CharField(max_length=16, null=False)
    password = models.CharField(max_length=37, null=False)
    server = models.CharField(max_length=50, null=True)

    def __unicode__(self):
        return self.task_tr_name

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User

try:
    from django.utils.timezone import now as datetime_now
except ImportError:
    datetime_now = datetime.datetime.now

SHA1_RE = re.compile('^[a-f0-9]{40}$')

class RegistrationManager(models.Manager):

    def activate_user(self, activation_key):

        if SHA1_RE.search(activation_key):
            try:
                profile = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not profile.activation_key_expired():
                user = profile.user
                user.is_active = True
                user.save()
                profile.activation_key = self.model.ACTIVATED
                profile.save()
                return user
            return False

    def create_inactive_user(self, username, email, password, site, send_email=True):

        new_user = User.objects.create_user(username=username, email=email, password=password)
        new_user.is_active = False
        new_user.save()

        registration_profile = self.create_profile(new_user)

        if send_email:
            registration_profile.send_activation_email(site)

        return new_user

    create_inactive_user = transaction.commit_on_success(create_inactive_user)

    def create_profile(self, user):

        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        username = user.username
        if isinstance(username, unicode):
            username = username.encode('utf-8')
        activation_key = hashlib.sha1(salt+username).hexdigest()
        return self.create(user=user, activation_key=activation_key)

    def delete_expired_users(self):

        for profile in self.all():
            try:
                if profile.activation_key_expired():
                    user = profile.user
                    if not user.is_active:
                        user.delete()
                        profile.delete()
            except User.DoesNotExist:
                profile.delete()


class RegistrationProfile(models.Model):

    ACTIVATED = u"ALREADY_ACTIVATED"

    user = models.ForeignKey(User, unique=True, verbose_name=_('user'))
    activation_key = models.CharField(_('activation key'), max_length=40)

    objects = RegistrationManager()

    class Meta:
        verbose_name = _('registration profile')
        verbose_name_plural = _('registration profiles')

    def __unicode__(self):
        return u"Registration information for %s" % self.user

    def activation_key_expired(self):

        expiration_date = datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.activation_key == self.ACTIVATED or (self.user.date_joined + expiration_date <= datetime_now())

    activation_key_expired.boolean = True

    def send_activation_email(self, site):

        ctx_dict = {'activation_key': self.activation_key, 'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                        'site': site}
        subject = render_to_string('accounts/activation_email_subject.txt', ctx_dict)
        subject = ''.join(subject.splitlines())
        message = render_to_string('accounts/activation_email.txt', ctx_dict)
        self.user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)

from django.core.files.storage import FileSystemStorage
fs = FileSystemStorage(location='/storage')

class UserProfile(models.Model):
    user = models.ForeignKey(User, null=False, primary_key=True)
    avatar = models.ImageField(blank=True, upload_to="user_resource", storage=fs, default='default/default_avatar.png')

    def __unicode__(self):
        return self.user

def create_profile(sender, **kwargs):
    user = kwargs.get('instance')
    if kwargs.get('created') and user.is_active:
        profile = UserProfile(user=user)
        profile.save()

post_save.connect(create_profile, sender=User)

@receiver(post_save, sender=User)
def create_user_api_key(sender, **kwargs):
     from tastypie.models import create_api_key
     user = kwargs.get('instance')
     if user.is_active:
        create_api_key(User, **kwargs)