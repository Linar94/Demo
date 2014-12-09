from django.contrib import admin
from accounts.models import *

class TaskTrView(admin.ModelAdmin):
    list_display = ('id', 'task_tr_name', 'username', 'password', 'server', 'user')

class UserProfileView(admin.ModelAdmin):
    list_display = ('user', 'avatar')

admin.site.register(TaskTr, TaskTrView)
admin.site.register(UserProfile, UserProfileView)
