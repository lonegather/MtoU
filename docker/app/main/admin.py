# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin
from . import models

# Register your models here.


class ProfileInline(admin.StackedInline):

    model = models.Profile
    can_delete = False
    verbose_name_plural = 'profile'


class CustomAdmin(UserAdmin):
    inlines = (ProfileInline, )


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'info')
    list_filter = ('name', )
    ordering = ('name', )
    
    
@admin.register(models.Genus)
class GenusAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'info')
    ordering = ('name', )
    

@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'info')
    list_filter = ('project', )
    ordering = ('genus', )


@admin.register(models.Entity)
class EntityAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'info', 'tag', 'genus', 'thumb')
    list_filter = ('tag', )
    ordering = ('name', )
    search_fields = ('name', )
    
    
@admin.register(models.Stage)
class StageAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'info', 'genus', 'source', 'data', 'project')
    list_filter = ('genus', 'project')
    ordering = ('name', )


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    
    list_display = ('entity', 'stage', 'path')
    list_filter = ('entity', 'stage')
    ordering = ('entity', )
    search_fields = ('entity', )


admin.site.unregister(User)
admin.site.register(User, CustomAdmin)
