import pyblish.api


class EntityCollector(pyblish.api.ContextPlugin):

    order = pyblish.api.CollectorOrder + 0.1
    label = "Collect Submit Content"

    def process(self, context):
        import json
        import time
        import samkit
        from maya import cmds

        context.set_data('label', cmds.optionVar(q='mtou_project'))
        submit_str = cmds.optionVar(q='mtou_submit')
        submit_list = json.loads(submit_str)
        for task in submit_list:
            instance = context.create_instance(task['entity'])
            instance.data['task'] = task
            instance.data['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            instance.data['family'] = task['stage']
            instance.data['pathSrc'] = samkit.get_source_path(task)
            instance.data['pathDat'] = samkit.get_data_path(task)

        for item in cmds.ls(type="unknown"):
            if cmds.objExists(item):
                cmds.delete(item)

        for up in cmds.unknownPlugin(q=True, list=True) or list():
            cmds.unknownPlugin(up, remove=True)

        cmds.file(save=True)


class EntityIntegrator(pyblish.api.InstancePlugin):

    order = pyblish.api.IntegratorOrder
    label = 'Submit'

    def process(self, instance):
        import os
        import json
        import shutil
        import samkit

        task = instance.data['task']
        samkit.open_file(task)

        current_path = samkit.get_local_path(task)
        source_path = instance.data['pathSrc']
        source_base = os.path.basename(source_path)
        source_dir = os.path.dirname(source_path)
        history_dir = os.path.join(source_dir, '.history')
        history_path = os.path.join(history_dir, '%s.json' % source_base)

        with open(history_path, 'r') as fp:
            history = json.load(fp)

        history['id'] = task['id']

        version = 0
        history_base = '%s.v%03d' % (os.path.join(history_dir, source_base), version)
        while os.path.exists(history_base):
            version += 1
            history_base = '%s.v%03d' % (os.path.join(history_dir, source_base), version)

        shutil.copyfile(source_path, history_base)

        history['history'].append({
            'time': history['time'],
            'version': version,
            'comment': history['comment']
        })
        history['time'] = instance.data['time']
        history['comment'] = instance.context.data['comment']

        with open(history_path, 'w') as fp:
            json.dump(history, fp, indent=2)

        shutil.copyfile(current_path, source_path)

        samkit.set_data('task', id=task['id'], owner='')
        samkit.new_file()
