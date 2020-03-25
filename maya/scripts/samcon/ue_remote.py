import json
import requests

if __name__ == '__main__':
    url = 'http://localhost:8080/remote/object/call'
    data = {
        "objectPath": "/Script/PythonScriptPlugin.Default__PythonScriptLibrary",
        "functionName": "ExecutePythonCommand",
        "parameters": {
            "pythonCommand": "print 'Hello from Maya'"
        }
    }
    resp = requests.put(url, json.dumps(data), headers={'content-type': 'application/json'}, verify=False)
    print(resp)
