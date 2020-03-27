import os
import json
import requests

if __name__ == '__main__':
    url = 'http://localhost:8080/remote/object/call'
    script_file = os.path.abspath(os.path.join(os.path.dirname(__file__), './scripts/integrate.py'))
    data = {
        "objectPath": "/Script/PythonScriptPlugin.Default__PythonScriptLibrary",
        "functionName": "ExecutePythonCommandEx",
        "parameters": {
            "pythonCommand": script_file
        }
    }
    resp = requests.put(url, json.dumps(data), headers={'content-type': 'application/json'}, verify=False)
    result = json.loads(resp.text)
    for output in result['LogOutput']:
        print(output['Output'])
