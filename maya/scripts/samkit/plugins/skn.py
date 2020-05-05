import pyblish.api


class SkinSkeletonValidator(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder - 0.38
    label = 'Validate Skeleton'
    families = ['skn', 'rig']

    def process(self, instance):
        from maya import cmds
        import samkit

        for root in cmds.ls(type='joint'):
            if root.count('UnrealRoot'):
                # Root found
                break
        else:
            assert False, 'Unable to locate \'UnrealRoot\'.'

        for rv in cmds.xform(root, q=True, rotation=True, ws=True):
            rv_str = '%.2f' % rv
            if rv_str != '0.00':
                self.log.info(root)
                assert False, 'Global rotation (including joint orient) of \'UnrealRoot\' is NOT 0.0'

        for tv in cmds.xform(root, q=True, translation=True, ws=True):
            tv_str = '%.2f' % tv
            if tv_str != '0.00':
                self.log.info(root)
                assert False, 'Global translation of \'UnrealRoot\' is NOT 0.0'

        try:
            cmds.getAttr('%s.UE_Skeleton' % root)
        except ValueError:
            cmds.addAttr(root, longName='UE_Skeleton', dataType='string', keyable=False)
        cmds.setAttr('%s.UE_Skeleton' % root, instance.context[0].data['name'], type='string')

        for bs in cmds.ls(type='blendShape'):
            for plug in cmds.listConnections('%s.weight' % bs, connections=True, p=True) or list():
                if plug.find('%s.' % bs) == 0:
                    attr = plug[(len(bs) + 1):]
                    dest = '%s.%s' % (root, attr)
                    try:
                        cmds.getAttr(dest)
                    except ValueError:
                        cmds.addAttr(root, ln=attr, at='double', dv=0)
                        cmds.setAttr(dest, keyable=True)
                        cmds.connectAttr(plug, dest, f=True)

        task = instance.data['task']
        samkit.open_file(task)


class SkinScaleValidator(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder - 0.37
    label = 'Validate Bone Scale'
    families = ['skn', 'rig']

    def process(self, instance):
        from maya import cmds
        import samkit

        task = instance.data['task']
        samkit.open_file(task)
        success = True

        for root in cmds.ls(type='joint'):
            if root.count('UnrealRoot'):
                joints = [joint for joint in cmds.listRelatives(root, allDescendents=True, type='joint')]
                break
        else:
            assert False, "Unable to locate \'UnrealRoot\'"

        for joint in joints:
            for sv in cmds.xform(joint, q=True, scale=True, ws=True):
                sv_str = '%.2f' % sv
                if sv_str != '1.00':
                    success = False
                    self.log.info(joint)
                    break

        assert success, 'Global scale of some joints are NOT 1.0'


class SkinHistoryValidator(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder - 0.36
    label = 'Validate Skin History'
    families = ['skn', 'rig']

    def process(self, instance):
        from maya import cmds
        import samkit

        task = instance.data['task']
        samkit.open_file(task)
        success = True
        shapes = cmds.ls(type='mesh', noIntermediate=True)
        assert len(shapes), 'No mesh found.'

        for shape in shapes:
            for node in cmds.listConnections(shape, d=False) or list():
                if cmds.objectType(node) not in [
                    'skinCluster',
                    'objectSet',
                    'tweak',
                    'groupId',
                    'transform',
                    'shadingEngine',
                    'groupParts',
                ]:
                    print(node + ':' + cmds.objectType(node))
                    success = False
                    self.log.info(shape)
                    break

        assert success, 'Some mesh have history other than SkinCluster or BlendShape.'


class SkinBlendShapeValidator(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder - 0.35
    label = 'Validate Skin BlendShape'
    families = ['skn', 'rig']

    def process(self, instance):
        from maya import cmds
        import samkit

        task = instance.data['task']
        samkit.open_file(task)
        success = True

        for bs in cmds.ls(type='blendShape'):
            for target in cmds.listConnections(bs, type='mesh', d=False) or list():
                for node in cmds.listConnections(target, d=False) or list():
                    if cmds.objectType(node) not in [
                        'tweak',
                        'groupId',
                        'transform',
                        'shadingEngine',
                        'groupParts',
                    ]:
                        success = False
                        self.log.info(target)
                        break

        assert success, 'BlendShape target must have NO history.'


class SkinExtractor(pyblish.api.InstancePlugin):

    order = pyblish.api.ExtractorOrder
    label = 'Export FBX Data'
    families = ['skn', 'rig']

    def process(self, instance):
        import os
        import shutil
        from maya import cmds, mel
        import samkit

        task = instance.data['task']
        samkit.open_file(task)

        current_path = samkit.get_local_path(task)
        current_dir = os.path.dirname(current_path)
        shutil.copyfile(current_path, os.path.join(current_dir, 'scene_cache.ma'))

        name = instance.data['name']
        path = instance.data['pathDat'].replace('\\', '/')
        if not os.path.exists(path):
            os.makedirs(path)

        instance.data['message'] = {
            'stage': task['stage'],
            'source': '{path}/{name}_skn.fbx'.format(**locals()),
            'target': '/Game/%s' % task['path'].split(';')[1],
            'skeleton': instance.data['name']
        }

        for root in cmds.ls(type='joint'):
            if root.count('UnrealRoot'):
                # Root found
                break
        else:
            assert False, 'Unable to locate \'UnrealRoot\'.'

        namespace = ':'+':'.join(root.split(':')[:-1])
        if namespace != ':':
            cmds.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)

        try:
            cmds.parent(root, world=True)
        except RuntimeError:
            pass

        selection_list = [root]
        for shape in cmds.ls(type='mesh', noIntermediate=True):
            for transform in cmds.listRelatives(shape, allParents=True):
                try:
                    cmds.parent(transform, world=True)
                except RuntimeError:
                    pass
                selection_list.append(transform)

        cmds.select(selection_list, r=True)

        mel.eval('FBXExportAnimationOnly -v false;')
        mel.eval('FBXExportAxisConversionMethod convertAnimation;')
        mel.eval('FBXExportCameras -v false;')
        mel.eval('FBXExportEmbeddedTextures -v true;')
        mel.eval('FBXExportFileVersion -v FBX201400;')
        mel.eval('FBXExportGenerateLog -v false;')
        mel.eval('FBXExportLights -v false;')
        mel.eval('FBXExportQuaternion -v quaternion;')
        mel.eval('FBXExportReferencedAssetsContent -v true;')
        mel.eval('FBXExportScaleFactor 1.0;')
        mel.eval('FBXExportShapes -v true;')
        mel.eval('FBXExportSkeletonDefinitions -v true;')
        mel.eval('FBXExportSkins -v true;')
        mel.eval('FBXExportSmoothingGroups -v true;')
        mel.eval('FBXExportSmoothMesh -v true;')
        mel.eval('FBXExportTangents -v true;')
        mel.eval('FBXExportUpAxis z;')
        mel.eval('FBXExportUseSceneName -v true;')
        mel.eval('FBXExport -f "%s" -s' % instance.data['message']['source'])

        samkit.ue_remote(instance.data['message'])

        samkit.open_file(task, True)


