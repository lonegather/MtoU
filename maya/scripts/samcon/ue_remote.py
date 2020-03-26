import os
import json
import requests
# from .utils import MODULE_PATH

if __name__ == '__main__':
    url = 'http://localhost:8080/remote/object/call'
    script_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../unreal/scripts/integrate.py'))
    data = {
        "objectPath": "/Script/PythonScriptPlugin.Default__PythonScriptLibrary",
        "functionName": "ExecutePythonCommandEx",
        "parameters": {
            "pythonCommand": script_file
        }
    }
    resp = requests.put(url, json.dumps(data), headers={'content-type': 'application/json'}, verify=False)
    print(json.loads(resp.text))
