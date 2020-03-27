import os
import json
import pickle
import socket
from socket import error
import requests
from requests.exceptions import ConnectionError
from maya import cmds

from .utils import *


session = requests.Session()


def auth_stats(host):
    return json.loads(session.get("http://%s/api/auth" % host).text)


def login(host, username, password):
    server = "http://%s/api/auth" % host
    kwargs = {
        'username': username,
        'password': password,
    }
    try:
        response = session.post(server, data=kwargs)
        if json.loads(response.text):
            cmds.optionVar(sv=(OPT_USERNAME, json.loads(response.text)['name']))
            cmds.optionVar(sv=(OPT_COOKIES, pickle.dumps(session.cookies)))
            return AUTH_SUCCESS
        else:
            cmds.optionVar(remove=OPT_USERNAME)
            cmds.optionVar(remove=OPT_COOKIES)
            return AUTH_FAILED
    except ConnectionError:
        return CONNECT_FAILED
    except ValueError:
        return CONNECT_FAILED


def logout():
    global session
    cmds.optionVar(remove=OPT_USERNAME)
    cmds.optionVar(remove=OPT_COOKIES)
    session.close()
    session = requests.Session()


def update(host, table, **fields):
    server = "http://%s/api" % host
    url = "{server}/{table}".format(**locals())
    kwargs = {'data': {}}
    for field in fields:
        if field == 'file':
            kwargs['files'] = fields[field]
        else:
            kwargs['data'][field] = fields[field]

    try:
        session.post(url, **kwargs)
        return True
    except ConnectionError:
        return False


def get_data(table, **filters):
    host = cmds.optionVar(q=OPT_HOST)
    url = 'http://%s/api/%s?' % (host, table)
    for field, value in filters.items():
        url += '{field}={value}&'.format(**locals())
    try:
        return json.loads(requests.get(url).text)
    except ValueError:
        return []
    except ConnectionError:
        return []


def set_data(table, **filters):
    host = cmds.optionVar(q=OPT_HOST)
    return update(host, table, **filters)


def ue_command(data=None):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('127.0.0.1', 8888))
    except error:
        return False
    if data:
        message = json.dumps(data)
        client.send('{message}\n'.format(**locals()).encode())
    client.close()
    return True


def ue_remote(data):
    url = 'http://localhost:8080/remote/object/call'
    body = {
        "objectPath": "/Script/PythonScriptPlugin.Default__PythonScriptLibrary",
        "functionName": "ExecutePythonCommandEx",
        "parameters": {
            "pythonCommand": os.path.abspath(os.path.join(MODULE_PATH, '../unreal/scripts/integrate.py'))
        }
    }
    resp = requests.put(url, json.dumps(body), headers={'content-type': 'application/json'}, verify=False)
    print(json.loads(resp.text))
