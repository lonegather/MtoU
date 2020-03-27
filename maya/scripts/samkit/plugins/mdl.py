import pyblish.api


'''
{'family': u'mdl',
 'name': u'Bobo',
 'pathDat': u'P:\\TEMPLATE\\UE\\asset\\CH\\Bobo',
 'pathSrc': u'P:\\TEMPLATE\\asset\\CH\\Bobo\\Bobo_mdl.ma',
 'time': '2019-07-05 16:04:19'}
'''


class ModelTypeValidator(pyblish.api.InstancePlugin):
    """
    Geometry should only be poly mesh.
    """

    order = pyblish.api.ValidatorOrder - 0.49
    label = 'Validate Model Type'
    families = ['mdl', 'skn']

    def process(self, instance):
        from maya import cmds
        import samkit

        task = instance.data['task']
        samkit.open_file(task)
        success = True

        assert cmds.ls(geometry=True, noIntermediate=True), 'No geometry found.'

        for shape in cmds.ls(geometry=True, noIntermediate=True):
            if cmds.objectType(shape) != 'mesh':
                success = False
                self.log.info(shape)

        assert success, 'Not all geometries are poly mesh.'


class ModelInstanceValidator(pyblish.api.InstancePlugin):
    """
    Geometry shape should have only one transform node.
    """

    order = pyblish.api.ValidatorOrder - 0.48
    label = 'Validate Model Instance'
    families = ['mdl', 'skn', 'rig']

    def process(self, instance):
        from maya import cmds
        import samkit

        task = instance.data['task']
        samkit.open_file(task)
        success = True

        for shape in cmds.ls(type='mesh', noIntermediate=True):
            transform = cmds.listRelatives(shape, allParents=True)
            if len(transform) > 1:
                success = False
                self.log.info(shape)

        assert success, 'Some geometries have multiple transform nodes.'


class ModelNameValidator(pyblish.api.InstancePlugin):
    """
    Geometry shape name should follow transform node.
    """

    order = pyblish.api.ValidatorOrder - 0.47
    label = 'Validate Model Naming'
    families = ['mdl']

    def process(self, instance):
        from maya import cmds
        import samkit

        task = instance.data['task']
        samkit.open_file(task)

        for shape in cmds.ls(type='mesh', noIntermediate=True):
            transform = cmds.listRelatives(shape, allParents=True)[0]
            shape_standard = transform + 'Shape'
            assert shape == shape_standard, \
                '%s\'s shape name should be %s.' % (transform, shape_standard)

    @staticmethod
    def fix(objects):
        from maya import cmds

        for shape in cmds.ls(type='mesh', noIntermediate=True):
            transform = cmds.listRelatives(shape, allParents=True)[0]
            shape_standard = transform + 'Shape'
            cmds.rename(shape, shape_standard)

        return True


class ModelTransformValidator(pyblish.api.InstancePlugin):
    """
    Geometry should have the scale value of 1.0.
    """

    order = pyblish.api.ValidatorOrder - 0.46
    label = 'Validate Model Scale'
    families = ['mdl', 'skn', 'rig']

    def process(self, instance):
        from maya import cmds
        import samkit

        task = instance.data['task']
        samkit.open_file(task)
        success = True

        for shape in cmds.ls(type='mesh', noIntermediate=True):
            transform = cmds.listRelatives(shape, allParents=True)[0]
            for sv in cmds.xform(transform, q=True, scale=True, ws=True):
                sv_str = '%.2f' % sv
                if sv_str != '1.00':
                    success = False
                    self.log.info(transform)
                    break

        assert success, 'Global scale of some mesh are NOT 1.0'


'''
class ModelUVSetValidator(pyblish.api.InstancePlugin):
    """
    Geometry should have only one UVSet.
    """

    order = pyblish.api.ValidatorOrder - 0.45
    label = 'Validate Model UVSet'
    families = ['mdl', 'skn', 'rig']

    def process(self, instance):
        from maya import cmds
        import samkit

        task = instance.data['task']
        samkit.open_file(task)
        success = True

        for shape in cmds.ls(type='mesh', noIntermediate=True):
            if len(cmds.polyUVSet(shape, q=True, auv=True)) > 1:
                success = False
                self.log.info(shape)

        assert success, 'Some mesh have multiply UVSets.'


class ModelColorSetValidator(pyblish.api.InstancePlugin):
    """
    Geometry should have no color set.
    """

    order = pyblish.api.ValidatorOrder - 0.44
    label = 'Validate Model Color Set'
    families = ['mdl', 'skn', 'rig']

    def process(self, instance):
        from maya import cmds
        import samkit

        task = instance.data['task']
        samkit.open_file(task)
        success = True

        for shape in cmds.ls(type='mesh', noIntermediate=True):
            if cmds.polyColorSet(shape, query=True, allColorSets=True):
                success = False
                self.log.info(shape)

        assert success, 'Some mesh have color sets.'

    @staticmethod
    def fix(objects):
        from maya import cmds

        for shape in cmds.ls(type='mesh', noIntermediate=True):
            for cs in cmds.polyColorSet(shape, query=True, allColorSets=True) or list():
                cmds.polyColorSet(shape, delete=True, colorSet=cs)
        return True
'''


class ModelHistoryValidator(pyblish.api.InstancePlugin):
    """
    Geometry should have no history.
    """

    order = pyblish.api.ValidatorOrder - 0.43
    label = 'Validate Model History'
    families = ['mdl']

    def process(self, instance):
        from maya import cmds
        import samkit

        task = instance.data['task']
        samkit.open_file(task)

        for shape in cmds.ls(type='mesh', noIntermediate=True):
            assert not cmds.listConnections(shape, d=False), \
                '%s has construction history.' % shape

    @staticmethod
    def fix(objects):
        from maya import cmds
        for shape in cmds.ls(type='mesh', noIntermediate=True):
            cmds.delete(shape, constructionHistory=True)
        return True


class ModelExtractor(pyblish.api.InstancePlugin):

    order = pyblish.api.ExtractorOrder
    label = 'Export FBX Data'
    families = ['mdl']

    def process(self, instance):
        import os
        from maya import cmds, mel
        import samkit

        task = instance.data['task']
        samkit.open_file(task)

        name = instance.data['name']
        path = instance.data['pathDat'].replace('\\', '/')
        if not os.path.exists(path):
            os.makedirs(path)

        instance.data['message'] = {
            'stage': task['stage'],
            'source': '{path}/{name}_mdl.fbx'.format(**locals()),
            'target': '/Game/%s' % task['path'].split(';')[1],
        }

        selection_list = []
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
        mel.eval('FBXExportEmbeddedTextures -v false;')
        mel.eval('FBXExportFileVersion -v FBX201400;')
        mel.eval('FBXExportGenerateLog -v false;')
        mel.eval('FBXExportLights -v false;')
        mel.eval('FBXExportQuaternion -v quaternion;')
        mel.eval('FBXExportReferencedAssetsContent -v true;')
        mel.eval('FBXExportScaleFactor 1.0;')
        mel.eval('FBXExportShapes -v true;')
        mel.eval('FBXExportSkeletonDefinitions -v false;')
        mel.eval('FBXExportSkins -v false;')
        mel.eval('FBXExportSmoothingGroups -v true;')
        mel.eval('FBXExportSmoothMesh -v true;')
        mel.eval('FBXExportTangents -v true;')
        mel.eval('FBXExportUpAxis z;')
        mel.eval('FBXExportUseSceneName -v true;')
        mel.eval('FBXExport -f "%s" -s' % instance.data['message']['source'])

        # samkit.ue_command(instance.data['message'])
        samkit.ue_remote(instance.data['message'])

        samkit.open_file(task, True)
