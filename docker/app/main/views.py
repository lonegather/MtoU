# -*- coding: utf-8 -*-

import os
import json
import markdown

from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from main import models


def renderer(func):
    def inner(request, project_id, **kwargs):
        try:
            current_project = models.Project.objects.get(id=project_id)
            request.session['current_project_id'] = str(project_id)
        except ObjectDoesNotExist:
            request.session['current_project_id'] = None
            return HttpResponseRedirect('/')

        context = func(request, current_project, **kwargs)
        context['current_path'] = request.path
        context['current_project'] = current_project
        context['projects'] = models.Project.all()
        context['genus_asset'] = models.Genus.objects.get(name='asset')
        context['genus_shot'] = models.Genus.objects.get(name='shot')
        context['genus_batch'] = models.Genus.objects.get(name='batch')
        context['user'] = request.user
        for key, val in request.GET.items():
            context[key] = val
        return render(request, context['page'], context)
    return inner


@renderer
def index_project(request, project, genus_id):
    try:
        current_genus = models.Genus.objects.get(id=genus_id)
    except ObjectDoesNotExist:
        current_genus = models.Genus.objects.get(name='asset')
    request.session['current_genus_id'] = str(current_genus.id)

    tags = models.Tag.objects.filter(genus=current_genus, project=project)
    entities = []
    for tag in tags:
        entities += models.Entity.objects.filter(tag=tag)
    return {
        'page': 'index.html',
        'current_genus': current_genus,
        'tags': tags,
        'entities': entities,
    }


@renderer
def index_entity(request, project, entity_id):
    entity = models.Entity.objects.get(id=entity_id)
    return {
        'page': 'entity_base.html',
        'entity': entity,
        'tasks': models.Task.objects.filter(entity=entity),
    }


@renderer
def settings(request, project):
    return {
        'page': 'settings.html',
        'tags': models.Tag.objects.filter(project=project),
        'stages': models.Stage.objects.filter(project=project),
    }


@renderer
def doc_episode(request, project, episode):
    request.session['current_episode'] = episode
    doc_dir = os.path.dirname(os.path.abspath(__file__))
    doc_file = os.path.abspath(os.path.join(doc_dir, '../static/markdown/%s.md' % episode))
    with open(doc_file, 'r', encoding='GBK') as f:
        return {
            'page': 'help.html',
            'doc': markdown.markdown(f.read(), extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
            ]),
            'current_episode': episode,
        }


def index(request):
    if not request.session.get('current_project_id', None):
        request.session['current_project_id'] = str(models.Project.all()[0]['id'])
    if not request.session.get('current_genus_id', None):
        request.session['current_genus_id'] = str(models.Genus.objects.all()[0].id)
    return HttpResponseRedirect(
        request.path +
        request.session['current_project_id'] + '/' +
        request.session['current_genus_id']
    )


def doc(request):
    if not request.session.get('current_project_id', None):
        request.session['current_project_id'] = str(models.Project.all()[0]['id'])
    if not request.session.get('current_episode', None):
        request.session['current_episode'] = '01_server_setup'
    return HttpResponseRedirect(
        '/' +
        request.session['current_project_id'] + '/help/' +
        request.session['current_episode']
    )


def user_login(request):
    if request.method == 'POST':
        username = request.POST['uname']
        password = request.POST['psw']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
        return HttpResponseRedirect(request.GET['next'])


def user_logout(request):
    logout(request)
    tokens = request.GET['next'].split('/')
    if 'settings' in tokens:
        tokens.remove('settings')
        return HttpResponseRedirect('/'.join(tokens))
    return HttpResponseRedirect(request.GET['next'])


def object_delete(request, object_id):
    print(request.path)
    return HttpResponseRedirect(request.GET['next'])


def api(request):
    table = request.path.split('/')[-1]
    if not table:
        return HttpResponse('')
    if table == 'auth':
        return api_auth(request)
    if request.method == 'GET':
        return api_get(request, table)
    elif request.method == 'POST':
        return api_set(request, table)


def api_get(request, table):
    flt = {}
    query_dict = {
        'project': models.Project.all,
        'entity': models.Entity.get,
        'stage': models.Stage.get,
        'task': models.Task.get,
        'genus': models.Genus.get,
        'tag': models.Tag.get,
    }
    for key in request.GET:
        flt[key] = request.GET[key]
    return HttpResponse(json.dumps(query_dict[table](**flt)))


def api_set(request, table):
    form = dict(request.POST)
    modify_dict = {
        'project': models.Project.set,
        'tag': models.Tag.set,
        'stage': models.Stage.set,
        'entity': models.Entity.set,
        'task': models.Task.set,
    }
    if request.FILES:
        for f in request.FILES:
            form[f] = request.FILES[f]
    modify_dict[table](form)
    return HttpResponseRedirect(request.GET['next'])


def api_auth(request):
    if request.method == 'GET':
        return HttpResponse(json.dumps(request.user.is_authenticated))
    elif request.method == 'POST':
        response = {}
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            response['session'] = request.session.session_key
            response['name'] = user.username
            try:
                response['info'] = user.profile.name
                response['role'] = user.profile.role.name
            except:
                pass

        return HttpResponse(json.dumps(response))
