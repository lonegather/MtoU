import pyblish.api


class AnimationFPSValidator(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder - 0.29
    label = 'Validate Animation FPS'
    families = ['lyt', 'anm']

    def process(self, instance):
        from maya import cmds

        assert cmds.currentUnit(q=True, time=True) == 'pal', \
            'Current FPS is NOT 25.'

    @staticmethod
    def fix(objects):
        from maya import cmds

        cmds.currentUnit(time='pal', updateAnimation=False)
        return True


class AnimationCameraValidator(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder - 0.28
    label = 'Validate Animation Camera'
    families = ['lyt', 'anm']

    def process(self, instance):
        from maya import cmds

        for shape in cmds.ls(type='camera'):
            cam = cmds.listRelatives(shape, allParents=True)[0]
            if cam == 'MainCam':
                break
        else:
            assert False, 'MainCam NOT found.'


class AnimationExtractor(pyblish.api.InstancePlugin):

    order = pyblish.api.ExtractorOrder
    label = 'Export FBX Data'
    families = ['lyt', 'anm']

    def process(self, instance):
        import os
        from maya import cmds, mel
        import samkit

        task = instance.data['task']
        samkit.open_file(task)

        name = instance.data['name']
        path = instance.data['pathDat'].replace('\\', '/')
        project = task['project']
        tag = task['tag']

        mint = int(cmds.playbackOptions(q=1, min=1))
        maxt = int(cmds.playbackOptions(q=1, max=1))
        mins = '%04d' % mint
        maxs = '%04d' % maxt

        if not os.path.exists(path):
            os.makedirs(path)

        for ref in cmds.ls(type='reference'):
            if ref != 'sharedReferenceNode':
                cmds.file(importReference=True, referenceNode=ref)

        mel.eval('FBXExportAnimationOnly -v false;')
        mel.eval('FBXExportApplyConstantKeyReducer -v false;')
        mel.eval('FBXExportBakeComplexStart -v %s;' % mint)
        mel.eval('FBXExportBakeComplexEnd -v %s;' % maxt)
        mel.eval('FBXExportBakeComplexStep -v 1;')
        mel.eval('FBXExportBakeResampleAnimation -v true;')
        mel.eval('FBXExportAxisConversionMethod convertAnimation;')
        mel.eval('FBXExportBakeComplexAnimation -v true;')
        mel.eval('FBXExportCameras -v false;')
        mel.eval('FBXExportConstraints -v false;')
        mel.eval('FBXExportEmbeddedTextures -v false;')
        mel.eval('FBXExportFileVersion -v FBX201400;')
        mel.eval('FBXExportGenerateLog -v false;')
        mel.eval('FBXExportLights -v false;')
        mel.eval('FBXExportQuaternion -v quaternion;')
        mel.eval('FBXExportReferencedAssetsContent -v false;')
        mel.eval('FBXExportScaleFactor 1.0;')
        mel.eval('FBXExportShapes -v false;')
        mel.eval('FBXExportSkeletonDefinitions -v false;')
        mel.eval('FBXExportSkins -v false;')
        mel.eval('FBXExportSmoothingGroups -v false;')
        mel.eval('FBXExportSmoothMesh -v false;')
        mel.eval('FBXExportTangents -v true;')
        mel.eval('FBXExportUpAxis z;')
        mel.eval('FBXExportUseSceneName -v true;')

        chars = []
        anims = []
        family = instance.data['family']
        for joint in cmds.ls(type='joint'):
            try:
                char = joint.split(':')[0]
                skel = cmds.getAttr('%s.UE_Skeleton' % joint)
                anim = '{project}_{tag}_{name}_{family}_{char}'.format(**locals())
                chars.append(skel)
                anims.append(anim)
                print('joint ------------ ' + joint)
                print('skel ------------ ' + skel)
                instance.data['message'] = {
                    'stage': task['stage'],
                    'source': '%s/%s.fbx' % (path, anim),
                    'target': '/Game/%s' % task['path'].split(';')[1],
                    'skeleton': skel,
                    'shot': {
                        'fps': 25.0,
                        'start': float(mint),
                        'end': float(maxt),
                    }
                }

            except ValueError:
                continue

            namespace = ':'+':'.join(joint.split(':')[:-1])

            cmds.select(joint, r=True)
            try:
                cmds.parent(joint, world=True)
            except: pass

            if namespace != ':':
                cmds.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)

            mel.eval('FBXExport -f "%s" -s' % instance.data['message']['source'])

            # samkit.ue_command(instance.data['message'])
            samkit.ue_remote(instance.data['message'])
            cmds.delete()

        try:
            instance.data['message'] = {
                'stage': 'cam',
                'source': '{path}/{project}_{tag}_{name}_{family}_MainCam_S{mins}_E{maxs}.fbx'.format(**locals()),
                'target': '/Game/%s' % task['path'].split(';')[1],
                'shot': {
                    'fps': 25.0,
                    'start': float(mint),
                    'end': float(maxt),
                    'chars': chars,
                    'anims': anims,
                    'aperture_width': cmds.getAttr('MainCamShape.horizontalFilmAperture'),
                    'aperture_height': cmds.getAttr('MainCamShape.verticalFilmAperture'),
                }
            }

            cmds.duplicate('MainCam', name='ShotCam')
            try: cmds.parent('ShotCam', world=True)
            except: pass
            cmds.xform('ShotCam', ra=[0.0, -90.0, 0.0], roo='xzy', p=True)
            cmds.parentConstraint('MainCam', 'ShotCam', mo=True)
            cmds.connectAttr('MainCamShape.focalLength', 'ShotCamShape.focalLength', f=True)

            cmds.select('ShotCam', r=True)
            cmds.setKeyframe('ShotCamShape.fl', t=['0sec'])
            mel.eval('FBXExportCameras -v true;')
            mel.eval('FBXExportUpAxis y;')
            mel.eval('FBXExportApplyConstantKeyReducer -v false;')
            mel.eval('FBXExport -f "%s" -s' % instance.data['message']['source'])

            # samkit.ue_command(instance.data['message'])
            samkit.ue_remote(instance.data['message'])

        except ValueError:
            pass
        print('cleanup')
        samkit.open_file(task, True)
