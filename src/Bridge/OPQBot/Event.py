from typing import *
from . import service
import time
import json
import requests
import base64
from Core.Event import ReceiveEvent
from Core.Event.MsgEvent import MsgEvent

from Core.Event.MsgEvent.MsgContent import MsgContent, TextMsg, AtMsg, PicMsg, PicMsgForword
from Core.Event.MsgEvent.MsgInfo import PrivateMsgInfo, GroupPrivateMsgInfo, GroupMsgInfo
from Core.Service.UserObj import *

from .webAPI import sendMsg

def OnSendMsg(event: ReceiveEvent):
    if isinstance(event.payload, MsgEvent):
        msg: MsgEvent = event.payload
    else:
        service.logger.warn("尝试发送的内容不是 MsgEvent")
        return
    starttime = time.time()
    # 初始化 Payload
    payload: Dict[str, Any] = {"groupid": 0,  # 仅临时会话需要
                               "atUser": 0}  # 有替代的方式了
    # 添加发送目标信息
    if isinstance(msg.msgInfo, GroupMsgInfo):
        payload = dict(payload, **{
            "toUser": msg.msgInfo.GroupId,
            "sendToType": 2,
        })
    if isinstance(msg.msgInfo, PrivateMsgInfo):
        payload = dict(payload, **{
            "toUser": msg.msgInfo.UserId,
            "sendToType": 1,
        })
    # 添加发送内容
    payload = dict(payload, **{
        "sendMsgType": "TextMsg",
        "content": "",
    })
    # 从消息链中组装信息正文
    for i, m in enumerate(msg.msgContent):
        if isinstance(m, TextMsg):
            payload['content'] += m.content
        elif isinstance(m, PicMsg):
            if m.forword.flag(service.config['qq']):
                payload = dict(payload, **{
                    "sendMsgType": "PicMsg",
                    "fileMd5": m.forword.flag,
                    "picUrl": "",
                    "picBase64Buf": "",
                })
            else:
                payload = dict(payload, **{
                    "sendMsgType": "PicMsg",
                    "picUrl": "",
                    "fileMd5": "",
                    "picBase64Buf": base64.b64encode(m.pic).decode()
                })
            if i == 0:
                payload['content'] += "[PICFLAG]"
        elif isinstance(m, AtMsg):
            payload['content'] += "[ATUSER(%s)]" % ",".join(m.atUser)
        else:
            service.logger.warn("消息链存在无法识别的消息内容：%s" % type(m))
    sendMsg(payload)
    endtime = time.time()
    if endtime - starttime < 0.9:
        time.sleep((1 - (endtime - starttime)))  # 每次处理信息间隔1000ms
