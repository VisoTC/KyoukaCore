from typing import *
from . import service
import requests
import json


api = "{host}/v1/LuaApiCaller".format(host=service.config['webapi'])


def sendMsg(payload):
    _payload = json.dumps(payload, ensure_ascii=False).encode()
    resp = requests.post(api, params={
        'qq': service.config['qq'],
        'funcname': 'SendMsg',
        'timeout': 10
    }, data=_payload)
    try:
        resp = resp.json()
        if resp.get('Ret', -1) != 0:
            service.logger.error(
                "sendMsg error: OPQBot API ERROR -> Ret: {} MSG: {}".format(resp.get('Ret', "UNKNOW"), resp.get('Msg', "UNKNOW")))
            return resp
    except:
        service.logger.error(
            "sendMsg error: OPQBot API ERROR -> " + resp.text)
