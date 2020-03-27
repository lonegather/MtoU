import unreal
from pprint import pprint

print('Hello from Maya')
for asset in unreal.EditorAssetLibrary.list_assets('/Game/'):
    print(asset)
