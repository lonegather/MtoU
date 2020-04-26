# -*- coding: utf-8 -*-

import json
import uuid

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User


__all__ = [
    'User',
    'Role',
    'Profile',
    'Project',
    'Genus',
    'Tag',
    'Entity',
    'Stage',
    'Task',
]


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, default='artist')
    info = models.CharField(max_length=50, default='artist')

    def __str__(self):
        return self.info


class Profile(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default='artist')
    role = models.ForeignKey(Role, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return 'User Information'


class Project(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    info = models.CharField(max_length=200, blank=True)
    fps = models.IntegerField(default=25)
    camera = models.CharField(max_length=50, default='MainCam')
    root = models.CharField(max_length=200, default='file:///P:')

    @classmethod
    def all(cls, *_, **__):
        result = []
        for prj in cls.objects.all():
            result.append({
                'id': str(prj.id),
                'name': prj.name,
                'info': prj.info,
                'root': prj.root,
            })
        return result

    @classmethod
    def set(cls, form):
        prj_id = form.get('id', [None])[0]

        if prj_id:
            prj = cls.objects.get(id=prj_id)
            prj.name = form.get('name', [prj.name])[0]
            prj.info = form.get('info', [prj.info])[0]
            prj.fps = int(form.get('fps', [prj.fps])[0])
            prj.camera = form.get('camera', [prj.camera])[0]
            prj.root = form.get('root', [prj.root])[0]
        else:
            prj = cls(
                name=form.get('name', ['undefined'])[0],
                info=form.get('info', [u'未命名'])[0],
                fps=int(form.get('fps', [30])[0]),
                camera=form.get('camera', ['MainCam'])[0],
                root=form.get('root', ['file:///P:'])[0],
            )
        prj.save()

    def save(self, *args, **kwargs):
        is_edit = len(Project.objects.filter(id=self.id))
        super(Project, self).save(*args, **kwargs)

        if is_edit:
            return

        gns_asset = Genus.objects.get(name='asset')
        gns_shot = Genus.objects.get(name='shot')
        gns_batch = Genus.objects.get(name='batch')
        Tag(
            project=self,
            genus=gns_batch,
            name='EP',
            info=u'集数'
        ).save()
        Tag(
            project=self,
            genus=gns_asset,
            name='CH',
            info=u'角色'
        ).save()
        Tag(
            project=self,
            genus=gns_asset,
            name='Prop',
            info=u'道具'
        ).save()
        Tag(
            project=self,
            genus=gns_asset,
            name='SC',
            info=u'场景'
        ).save()
        Stage(
            project=self,
            genus=gns_asset,
            name='mdl',
            info=u'模型',
            source='{project}/{genus}/{tag}/{entity}/{entity}_{stage}.ma',
            data='{project}/{genus}/{tag}/{entity}/',
        ).save()
        Stage(
            project=self,
            genus=gns_asset,
            name='rig',
            info=u'绑定',
            source='{project}/{genus}/{tag}/{entity}/{entity}_{stage}.ma',
            data='{project}/{genus}/{tag}/{entity}/',
        ).save()
        Stage(
            project=self,
            genus=gns_shot,
            name='lyt',
            info=u'布局',
            source='{project}/{genus}/source/{project}_{tag}_{entity}_layout.ma',
            data='{project}/{genus}/{tag}/{entity}/',
        ).save()
        Stage(
            project=self,
            genus=gns_shot,
            name='anm',
            info=u'动画',
            source='{project}/{genus}/source/{project}_{tag}_{entity}.ma',
            data='{project}/{genus}/{tag}/{entity}/',
        ).save()
    
    def __str__(self):
        return self.name
    

class Genus(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=10)
    info = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.name

    @classmethod
    def get(cls, **kwargs):
        result = []
        keywords = {}
        mapper = {}
        for key in kwargs:
            if key in mapper:
                keywords[mapper[key]] = kwargs[key]
            else:
                keywords[key] = kwargs[key]
        for genus in cls.objects.filter(**keywords):
            result.append({
                'id': str(genus.id),
                'name': genus.name,
                'info': genus.info,
            })
        return result
    

class Tag(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    genus = models.ForeignKey(Genus, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    info = models.CharField(max_length=50, blank=True)

    @classmethod
    def get(cls, **kwargs):
        result = []
        keywords = {}
        mapper = {
            'project_id': 'project__id',
            'project': 'project__name',
            'genus_id': 'genus__id',
            'genus': 'genus__name',
        }
        for key in kwargs:
            if key in mapper:
                keywords[mapper[key]] = uuid.UUID(kwargs[key]) if key in ['project_id', 'genus_id'] else kwargs[key]
            else:
                keywords[key] = uuid.UUID(kwargs[key]) if key == 'id' else kwargs[key]
        for tag in cls.objects.filter(**keywords):
            result.append({
                'id': str(tag.id),
                'name': tag.name,
                'info': tag.info,
                'genus_id': str(tag.genus.id),
                'genus_name': tag.genus.name,
                'genus_info': tag.genus.info,
            })
        return result

    @classmethod
    def set(cls, form):
        prj_id = form['project_id'][0]
        prj = Project.objects.get(id=prj_id)
        genus_name = form['genus_name'][0]
        gns = Genus.objects.get(name=genus_name)
        if form.get('id', [None])[0]:
            tag = cls.objects.get(id=form['id'][0])
            tag.name = form['name'][0]
            tag.info = form['info'][0]
            tag.project = prj
            tag.genus = gns
        else:
            tag = cls(
                project=prj,
                genus=gns,
                name=form.get('name', ['undefined'])[0],
                info=form.get('info', [u'未命名'])[0],
            )
        tag.save()
    
    def __str__(self):
        return self.name if self.project.name == '|' else '%s | %s' % (self.project, self.name)


class Entity(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.ForeignKey(Tag, default=uuid.uuid4, on_delete=models.CASCADE)
    link = models.ManyToManyField("Entity", blank=True)
    name = models.CharField(max_length=100)
    info = models.CharField(max_length=200, blank=True)
    thumb = models.ImageField(upload_to="thumbs", default="thumbs/default.png")

    @classmethod
    def get(cls, **kwargs):
        result = []
        keywords = {}
        mapper = {
            'project_id': 'tag__project__id',
            'project': 'tag__project__name',
            'genus': 'tag__genus__name',
            'tag_id': 'tag__id',
            'tag': 'tag__name',
        }
        for key in kwargs:
            if key in mapper:
                keywords[mapper[key]] = uuid.UUID(kwargs[key]) if key in ['project_id'] else kwargs[key]
            else:
                keywords[key] = uuid.UUID(kwargs[key]) if key == 'id' else kwargs[key]
        for ent in cls.objects.filter(**keywords):
            link = []
            for l in ent.link.all():
                link.append(str(l.id))

            result.append({
                'id': str(ent.id),
                'name': ent.name,
                'info': ent.info,
                'project_id': str(ent.tag.project.id),
                'genus_id': str(ent.tag.genus.id),
                'genus_name': ent.tag.genus.name,
                'genus_info': ent.tag.genus.info,
                'tag_id': str(ent.tag.id),
                'tag_name': ent.tag.name,
                'tag_info': ent.tag.info,
                'link': link,
                'thumb': ent.thumb.url,
            })
        return result

    @classmethod
    def get_by_id(cls, id_list):
        result = []
        id_list = json.loads(id_list)
        for i in id_list:
            link = []
            ent = cls.objects.get(id=i)
            for l in ent.link.all():
                link.append(str(l.id))
            result.append({
                'id': str(ent.id),
                'project': ent.tag.project.name,
                'name': ent.name,
                'info': ent.info,
                'genus': ent.tag.genus.name,
                'genus_info': ent.tag.genus.info,
                'tag': ent.tag.name,
                'tag_info': ent.tag.info,
                'link': link,
                'thumb': ent.thumb.url,
            })
        return result

    @classmethod
    def set(cls, form):
        ent_id = form.get('id', [None])[0]
        del_method = form.get('delete', False)

        if del_method and ent_id:
            ent = Entity.objects.get(id=ent_id)
            ent.delete()
            return

        tag = Tag.objects.get(id=form['tag_id'][0])

        if ent_id:
            ent = Entity.objects.get(id=ent_id)
            ent.name = form['name'][0]
            ent.info = form['info'][0]
            ent.tag = tag
            ent.link.clear()
        else:
            ent = Entity(
                tag=tag,
                name=form['name'][0],
                info=form['info'][0]
            )
            ent.save()

        for link_id in form.get('link', []):
            link = Entity.objects.get(id=link_id)
            ent.link.add(link)

        if 'thumb' in form:
            ent.thumb = form['thumb']

        ent.save()
    
    def genus(self):
        return self.tag.genus
    
    def save(self, *args, **kwargs):
        project = self.tag.project
        if self.genus().name == 'batch':
            tags = Tag.objects.filter(name=self.name, project=project)
            if not len(tags):
                genus = Genus.objects.get(name='shot')
                data = {
                    'name': self.name,
                    'project': project,
                    'genus': genus,
                    'info': self.info
                }
                Tag(**data).save()
            else:
                tag = tags[0]
                tag.info = self.info
                tag.save()

        super(Entity, self).save(*args, **kwargs)

        if Task.objects.filter(entity=self):
            return

        for stage in Stage.objects.filter(genus=self.genus(), project=project):
            data = {
                'entity': self,
                'stage': stage,
            }
            Task(**data).save()
        
    def delete(self, using=None, keep_parents=False):
        if self.genus().name == 'batch':
            Tag.objects.get(project=self.tag.project, name=self.name).delete()
        
        return super(Entity, self).delete(using=using, keep_parents=keep_parents)
    
    def __str__(self):
        name = str(self.name)
        project = str(self.tag.project)
        tag = str(self.tag.name)
        return '{name} [ {project} | {tag} ]'.format(**locals())


class Stage(models.Model):

    @classmethod
    def get(cls, **kwargs):
        result = []
        keywords = {}
        mapper = {'project': 'project__name',
                  'genus': 'genus__name',
                  }
        for key in kwargs:
            if key in mapper:
                keywords[mapper[key]] = uuid.UUID(kwargs[key]) if key in [] else kwargs[key]
            else:
                keywords[key] = uuid.UUID(kwargs[key]) if key == 'id' else kwargs[key]
        for stg in cls.objects.filter(**keywords):
            result.append({'name': stg.name, 'info': stg.info, 'project': stg.project.name,
                           'genus': stg.genus.name, 'genus_info': stg.genus.info,
                           'source': stg.source, 'data': stg.data})
        return result

    @classmethod
    def set(cls, form):
        prj_id = form['project_id'][0]
        prj = Project.objects.get(id=prj_id)
        genus_name = form['genus_name'][0]
        gns = Genus.objects.get(name=genus_name)
        if form.get('id', [None])[0]:
            stg = cls.objects.get(id=form['id'][0])
            stg.name = form['name'][0]
            stg.info = form['info'][0]
            stg.source = form['source'][0]
            stg.data = form['data'][0]
            stg.project = prj
            stg.genus = gns
        else:
            stg = cls(
                project=prj,
                genus=gns,
                name=form.get('name', ['undefined'])[0],
                info=form.get('info', [u'未命名'])[0],
                source=form.get('source', [''])[0],
                data=form.get('data', [''])[0],
            )
        stg.save()
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, default=uuid.uuid4, on_delete=models.CASCADE)
    genus = models.ForeignKey(Genus, default=uuid.uuid4, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    info = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=200, default='/')
    data = models.CharField(max_length=200, default='/')

    def __str__(self):
        return self.name
    

class Task(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(Entity, default=uuid.uuid4, on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, default=uuid.uuid4, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)

    @classmethod
    def get(cls, **kwargs):
        result = []
        keywords = {}
        mapper = {
            'project': 'stage__project__name',
            'genus': 'genus__name',
            'stage': 'stage__name',
            'entity': 'entity__name',
            'entity_id': 'entity__id',
            'owner': 'owner__username',
        }
        for key in kwargs:
            if key in mapper:
                keywords[mapper[key]] = uuid.UUID(kwargs[key]) if key in ['entity_id'] else kwargs[key]
            else:
                keywords[key] = uuid.UUID(kwargs[key]) if key == 'id' else kwargs[key]

        for tsk in cls.objects.filter(**keywords):
            result.append({
                'id': str(tsk.id),
                'project': tsk.stage.project.name,
                'genus': tsk.stage.genus.name,
                'genus_info': tsk.stage.genus.info,
                'tag': tsk.entity.tag.name,
                'tag_info': tsk.entity.tag.info,
                'entity': tsk.entity.name,
                'entity_info': tsk.entity.info,
                'stage': tsk.stage.name,
                'stage_info': tsk.stage.info,
                'path': tsk.path(),
                'owner': str(tsk.owner.username if tsk.owner else ''),
            })
        return result

    def path(self):
        root = self.stage.project.root
        project = self.stage.project.name
        tag = self.entity.tag.name
        genus = self.stage.genus.name
        entity = self.entity.name
        stage = self.stage.name
        return ';'.join((
            self.stage.source.format(**locals()),
            self.stage.data.format(**locals())
        ))

    @classmethod
    def set(cls, form):
        tsk_id = form.get('id', [None])[0]
        username = form.get('owner', [''])[0]

        if tsk_id:
            tsk = cls.objects.get(id=tsk_id)
            try:
                tsk.owner = User.objects.get(username=username)
            except ObjectDoesNotExist:
                if 'owner' in form:
                    tsk.owner = None

        else:
            # TODO: Create new task
            pass

        tsk.save()

    @classmethod
    def setup(cls, entity, stage=None):
        project = entity.tag.project
    
    def __str__(self):
        return '%s - %s' % (self.stage.name, self.entity)
