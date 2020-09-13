from typing import List
from . import service
import socketio
import time
import json

from .qqList import getFriendAndGroupList

from Core.Event import Eventer, ServiceType, ReceiveEvent

from Core.Event.MsgEvent import MsgEvent
from Core.Event.MsgEvent.MsgContent import MsgContent, TextMsg, AtMsg, PicMsg, PicMsgForword
from Core.Event.MsgEvent.MsgInfo import PrivateMsgInfo, GroupPrivateMsgInfo, GroupMsgInfo
import threading

sio = socketio.Client()
sioReady = threading.Event()


@sio.on('connect')
def OnConnect():
    service.logger.info(
        '已连接到 OPQBot, 开始获取 QQ: {} 的会话'.format(service.config['qq']))
    sio.emit('GetWebConn', service.config['qq'],
             callback=GetWebConnCallBack)  # 取得当前已经登录的QQ链接


def GetWebConnCallBack(data):
    if data == "OK" or data == '当前已存在活动的WebSocket 已为您切换当前Socket':
        service.logger.info('获取 QQ: {} 的会话成功！'.format(service.config['qq']))
        getFriendAndGroupList()
        sioReady.set()
    else:
        service.logger.error(
            '获取 QQ: {} 的会话失败：{}'.format(service.config['qq'], data))


@sio.on('OnFriendMsgs')
def OnFriendMsgs(payload):
    try:
        if not 'Data' in payload['CurrentPacket'].keys():  # TODO：暂时所有非聊天信息
            return
        if payload['CurrentPacket']['Data']['FromUin'] == payload['CurrentQQ']:  # 若是自己发送的消息直接忽略
            return
        if payload['CurrentPacket']['Data']['MsgType'] == "TextMsg":
            tmp = MsgEvent(**{"msgInfo": PrivateMsgInfo(**{
                "UserId": payload['CurrentPacket']['Data']['FromUin'],
                "UserName": service.api.FriendsList.get(payload['CurrentPacket']['Data']['FromUin']),
            }),
                "msgContent": TextMsg(payload['CurrentPacket']['Data']['Content']),
                "otherData": {
                "MsgSeq": payload['CurrentPacket']['Data']['MsgSeq'],
            }
            })
        else:
            service.logger.info(json.dumps(payload))
            return
        service.api.sendMsg(Eventer('*', ServiceType.Plugin), tmp)
    except Exception as e:
        service.logger.exception(e)  # 遇到问题咋们就逃避就行了
        return


@sio.on('OnGroupMsgs')
def OnGroupMsgs(payload):
    try:
        if not 'Data' in payload['CurrentPacket'].keys():  # TODO：暂时所有非聊天信息
            return
        if payload['CurrentPacket']['Data']['FromUserId'] == payload['CurrentQQ']:  # 若是自己发送的消息直接忽略
            return
        if payload['CurrentPacket']['Data']['MsgType'] == "TextMsg":
            tmp = MsgEvent(**{"msgInfo": GroupMsgInfo(**{
                "GroupId": payload['CurrentPacket']['Data']['FromGroupId'],
                "GroupName": payload['CurrentPacket']['Data']['FromGroupName'],
                "UserId": payload['CurrentPacket']['Data']['FromUserId'],
                "UserName": payload['CurrentPacket']['Data']['FromNickName'],
            }),
                "msgContent": TextMsg(payload['CurrentPacket']['Data']['Content']),
                "otherData": {
                "MsgSeq": payload['CurrentPacket']['Data']['MsgSeq'],
                "MsgRandom": payload['CurrentPacket']['Data']['MsgRandom'],
            }
            })
        elif payload['CurrentPacket']['Data']['MsgType'] == "AtMsg":
            atContent = json.loads(
                payload['CurrentPacket']['Data']['Content'])
            Content: List[MsgContent] = [TextMsg(atContent['Content'])]
            for aUser in atContent.get('UserID', []):
                Content.append(AtMsg(aUser))
            tmp = MsgEvent(**{"msgInfo": GroupMsgInfo(**{
                "GroupId": payload['CurrentPacket']['Data']['FromGroupId'],
                "GroupName": payload['CurrentPacket']['Data']['FromGroupName'],
                "UserId": payload['CurrentPacket']['Data']['FromUserId'],
                "UserName": payload['CurrentPacket']['Data']['FromNickName'],
            }),
                "msgContent": Content,
                "otherData": {
                "MsgSeq": payload['CurrentPacket']['Data']['MsgSeq'],
                "MsgRandom": payload['CurrentPacket']['Data']['MsgRandom'],
            }
            })
        # TODO: 需要了解图片和文字是同一条消息的情况
        elif payload['CurrentPacket']['Data']['MsgType'] == "PicMsg":
            msgLink = []
            picContent = json.loads(
                payload['CurrentPacket']['Data']['Content'])
            for pic in picContent['GroupPic']:
                msgLink.append(PicMsg.webImg(
                    pic['Url'], {}, PicMsgForword(service.config['qq'], pic['FileMd5'])))
            if 'Content' in picContent:
                msgLink.append(TextMsg(picContent['Content']))
            tmp = MsgEvent(**{"msgInfo": GroupMsgInfo(**{
                "GroupId": payload['CurrentPacket']['Data']['FromGroupId'],
                "GroupName": payload['CurrentPacket']['Data']['FromGroupName'],
                "UserId": payload['CurrentPacket']['Data']['FromUserId'],
                "UserName": payload['CurrentPacket']['Data']['FromNickName'],
            }),
                "msgContent": msgLink,
                "otherData": {
                "MsgSeq": payload['CurrentPacket']['Data']['MsgSeq'],
                "MsgRandom": payload['CurrentPacket']['Data']['MsgRandom'],
            }
            })
        else:
            # self.logger.info(json.dumps(payload))
            return
        service.api.sendMsg(Eventer("*", ServiceType.Plugin), tmp)
    except Exception as e:
        service.logger.exception(e)  # 遇到问题咋们就逃避就行了
        return


@sio.on('OnEvents')
def OnEvents(payload): ...
# print("OnEvents")
# print(payload)
