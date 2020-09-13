import logging
import time
from typing import *
from .initServer import service
from .socketio import sio, sioReady
from .Event import OnSendMsg
import socketio
import socketio.exceptions

from Core.Event.MsgEvent.MsgInfo import PrivateMsgInfo, GroupPrivateMsgInfo, GroupMsgInfo

logging.getLogger('engineio.client').setLevel(logging.ERROR)
logging.getLogger('socketio.client').setLevel(logging.ERROR)

service.register(PrivateMsgInfo,OnSendMsg)
service.register(GroupPrivateMsgInfo,OnSendMsg)
service.register(GroupMsgInfo,OnSendMsg)

if not service.config['qq'] == "在此输入qq号" or service.config['qq'].isdigit():
    try:
        sio.connect('http://127.0.0.1:8888', transports=['websocket'])
    except socketio.exceptions.ConnectionError:
        service.initDone(service.config['qq'],False,True,msg="无法连接到 OPQBot，请检查 webapi 是否正确")

    if sioReady.wait(timeout=5):
        service.initDone(service.config['qq'], True)
    else:
        service.initDone(service.config['qq'], False, True, msg="获得会话超时")


else:
    service.initDone(service.config['qq'], False,
                     True, msg="配置文件错误：需要是正确的qq号码")
