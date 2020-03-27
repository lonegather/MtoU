import os
import json
import unreal
from pprint import pprint

if __name__ == '__main__':
    with open(os.path.dirname(__file__) + '/option.json') as option:
        data = json.load(option)
        data['target'] = data['target'][:-1] if data['target'][-1] in ['\\', '/'] else data['target']

    print('-' * 80)
    for k, v in data.items():
        print('[%s] --- %s' % (k, v))

    # import fbx
    factory = unreal.FbxFactory()
    task = unreal.AssetImportTask()
    asset_tool = unreal.AssetToolsHelpers.get_asset_tools()

    task.set_editor_property('automated', True)
    task.set_editor_property('destination_path', data['target'])
    task.set_editor_property('factory', factory)
    task.set_editor_property('filename', data['source'])
    task.set_editor_property('save', True)
    asset_tool.import_asset_tasks([task])
