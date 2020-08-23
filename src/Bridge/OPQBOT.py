from Core.Interface.UserObj import Group, GroupMember, GroupMembers, Groups, User, Users
import asyncio
import time
import socketio
import requests
import json
import threading
from Core.Interface.IBridge import IBridge
from Core.Interface.Msg.MsgBase import MsgEvent
from Core.Interface.Msg.MsgInfo import GroupMsgInfo, PrivateMsgInfo
from Core.Interface.Msg.MsgContent import AtMsg, MsgContent, PicMsg, TextMsg


class OPQBOT(IBridge):

    @staticmethod
    def PluginInfo():
        '''
        插件信息
        :return Config
        '''
        return {
            "packageName": "com.visotc.KyoukaCore.Brdge.OPQBOT",  # 包名，唯一标识
            "name": "OPQBOT Bot Bridge",  # 显示名称
            "version": "dev",  # 版本号
            "author": "Viso-TC",  # 作者
            "entrance": OPQBOT  # 入口类
        }

    @property
    def pluginInfo(self):
        return self.PluginInfo()

    @property
    def _api(
        self): return "{host}/v1/LuaApiCaller".format(host=self.apiUrl)

    sio = socketio.Client()
    qq = '1622376821'
    apiUrl = "http://127.0.0.1:8888"

    def OnFriendMsgs(self, payload):
        try:
            if not 'Data' in payload['CurrentPacket'].keys():  # TODO：暂时所有非聊天信息
                return
            if payload['CurrentPacket']['Data']['FromUin'] == payload['CurrentQQ']:  # 若是自己发送的消息直接忽略
                return
            if payload['CurrentPacket']['Data']['MsgType'] == "TextMsg":
                tmp = MsgEvent(**{"bridge": payload['CurrentQQ'],
                                  "time": int(time.time()),
                                  "msgInfo": PrivateMsgInfo(**{
                                      "UserId": payload['CurrentPacket']['Data']['FromUin'],
                                      "UserName": self._IBridge__UserList.get(payload['CurrentPacket']['Data']['FromUin']),
                                  }),
                                  "msgContent": TextMsg(payload['CurrentPacket']['Data']['Content'])
                                  })
            elif payload['CurrentPacket']['Data']['MsgType'] == "AtMsg":
                atContent = json.loads(
                    payload['CurrentPacket']['Data']['Content'])
                tmp = MsgEvent(**{"bridge": payload['CurrentQQ'],
                                  "time": int(time.time()),
                                  "msgInfo": PrivateMsgInfo(**{
                                      "UserId": payload['CurrentPacket']['Data']['FromUin'],
                                      "UserName": self._IBridge__UserList.get(payload['CurrentPacket']['Data']['FromUin']),
                                  }),
                                  "msgContent": TextMsg(atContent['Content'], atUser=atContent.get('UserID', None)),
                                  })
            else:
                self.logger.info(json.dumps(payload))
                return
            self.msgBusPort.send(tmp)
        except Exception as e:
            self.logger.exception(e)  # 遇到问题咋们就逃避就行了
            return

    def OnGroupMsgs(self, payload):
        try:
            if not 'Data' in payload['CurrentPacket'].keys():  # TODO：暂时所有非聊天信息
                return
            if payload['CurrentPacket']['Data']['FromUserId'] == payload['CurrentQQ']:  # 若是自己发送的消息直接忽略
                return
            if payload['CurrentPacket']['Data']['MsgType'] == "TextMsg":
                tmp = MsgEvent(**{"bridge": payload['CurrentQQ'],
                                  "time": int(time.time()),
                                  "msgInfo": GroupMsgInfo(**{
                                      "GroupId": payload['CurrentPacket']['Data']['FromGroupId'],
                                      "GroupName": payload['CurrentPacket']['Data']['FromGroupName'],
                                      "UserId": payload['CurrentPacket']['Data']['FromUserId'],
                                      "UserName": payload['CurrentPacket']['Data']['FromNickName'],
                                  }),
                                  "msgContent": TextMsg(payload['CurrentPacket']['Data']['Content'])
                                  })
            elif payload['CurrentPacket']['Data']['MsgType'] == "AtMsg":
                atContent = json.loads(
                    payload['CurrentPacket']['Data']['Content'])
                tmp = MsgEvent(**{"bridge": payload['CurrentQQ'],
                                  "time": int(time.time()),
                                  "msgInfo": GroupMsgInfo(**{
                                      "GroupId": payload['CurrentPacket']['Data']['FromGroupId'],
                                      "GroupName": payload['CurrentPacket']['Data']['FromGroupName'],
                                      "UserId": payload['CurrentPacket']['Data']['FromUserId'],
                                      "UserName": payload['CurrentPacket']['Data']['FromNickName'],
                                  }),
                                  "msgContent": TextMsg(atContent['Content'], atUser=atContent.get('UserID', None)),
                                  })
            else:
                self.logger.info(json.dumps(payload))
                return
            self.msgBusPort.send(tmp)
        except Exception as e:
            self.logger.exception(e)  # 遇到问题咋们就逃避就行了
            return

    def OnEvents(self, payload):
        print("OnEvents")
        print(payload)

    def sendMsg(self, payload):
        _payload = json.dumps(payload, ensure_ascii=False)
        resp = requests.post(self._api, params={
            'qq': self.qq,
            'funcname': 'SendMsg',
            'timeout': 10
        }, data=_payload.encode("UTF-8"))
        try:
            resp = resp.json()
            if resp.get('Ret', -1) != 0:
                self.__opqObj.logger.error(
                    "sendMsg error:{} @ {}".format(resp.get('Ret', "UNKNOW"), resp.get('Msg', "UNKNOW")))
            return resp
        except ValueError:
            self.__opqObj.logger.error(
                "sendMsg error: OPQBot API ERROR -> " + resp.text())

    def OnSendMsg(self, msg):
        starttime = time.time()*1000
        # 初始化 Payload
        payload = {"groupid": 0,  # 仅临时会话需要
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
        for m in msg.msgContent:
            if isinstance(m, TextMsg):
                payload['content'] += m.content
            elif isinstance(m, PicMsg):
                payload['content'] += "[PICFLAG]"
                if not m.forword is None:
                    payload = dict(payload, **{
                        "fileMd5": m.forword
                    })
                else:
                    payload = dict(payload, **{
                        "picBase64Buf": m.pic
                    })
            elif isinstance(m, AtMsg):
                payload['content'] += "[ATUSER(%s)]" % ",".join(m.atUser)
            else:
                self.logger.warn("消息链存在无法识别的消息内容：%s" % type(m))
        if isinstance(msg.msgContent, TextMsg):
            if len(msg.msgContent.atUser) > 0:
                payload = dict(payload, **{
                    "sendMsgType": "TextMsg",
                    "content": "[ATUSER({})]\n{}".format(",".join(msg.msgContent.atUser), msg.msgContent.content),
                })
            else:
                payload = dict(payload, **{
                    "sendMsgType": "TextMsg",
                    "content": msg.msgContent.content,
                })
        self.sendMsg(payload)
        endtime = time.time()*1000
        if endtime - starttime < 900:
            time.sleep(900 - (endtime - starttime))  # 每次处理信息间隔900ms
            ...

    def __del__(self):
        self.sio.disconnect()

    def getFriendAndGroupList(self):
        """
        载入用户列表与群组列表
        """
        self._IBridge__UserList = self.getUserList()
        self._IBridge__GroupList = self.getGroupList()

    def getUserList(self):
        i = -1
        FriendList = Users()
        while i != 0:
            if i == -1:
                i = 0
            _payload = json.dumps({"StartIndex": i}, ensure_ascii=False)
            resp = requests.post(self._api, params={
                'qq': self.qq,
                'funcname': 'GetQQUserList',
                'timeout': 10
            }, data=_payload.encode("UTF-8"))
            result = resp.json()
            for u in result['Friendlist']:
                FriendList.append(
                    User(u['FriendUin'], u['NickName'])
                )
            i = result['StartIndex']
        return FriendList

    def getGroupList(self):
        NextToken = None
        GroupList = Groups()
        while NextToken != "":
            if NextToken == None:
                NextToken = ""
            _payload = json.dumps({"NextToken": NextToken}, ensure_ascii=False)
            resp = requests.post(self._api, params={
                'qq': self.qq,
                'funcname': 'GetGroupList',
                'timeout': 10
            }, data=_payload.encode("UTF-8"))
            result = resp.json()
            for g in result['TroopList']:
                GroupList.append(
                    Group(g['GroupId'],g['GroupName'],g['GroupOwner'],self.getGroupMemberList(g['GroupId']))
                )
            NextToken = result['NextToken']
        return GroupList

    def getGroupMemberList(self, gid: int):
        LastUin = -1
        MemberList = GroupMembers()
        while LastUin != 0:
            if LastUin == -1:
                LastUin == 0
            _payload = json.dumps(
                {"GroupUin": int(gid), "LastUin": LastUin}, ensure_ascii=False)
            resp = requests.post(self._api, params={
                'qq': self.qq,
                'funcname': 'GetGroupUserList',
                'timeout': 10
            }, data=_payload.encode("UTF-8"))
            result = resp.json()
            for gm in result['MemberList']:
                MemberList.append(
                    GroupMember(gm['MemberUin'],
                                gm['GroupCard'] if gm['GroupCard'] != "" else gm['NickName'],
                                gm['GroupAdmin'] == 1)
                )
            LastUin = result['LastUin']
        return MemberList

    def run(self):
        '''
        插件逻辑由此开始，需要自己负责实现各类方法
        '''
        self.logger.info("start")
        self.config['uid'] = self.qq
        self.config.commit()
        # 绑定回调
        self.callback(self.OnSendMsg, GroupMsgInfo)
        self.callback(self.OnSendMsg, PrivateMsgInfo)
        # 初始化 Socket-io 并链接到OPQBot
        self.sio.register_namespace(OPQBOTSio(self))
        self.sio.connect('http://127.0.0.1:8888', transports=['websocket'])


class OPQBOTSio(socketio.ClientNamespace):
    def __init__(self, opqBot: OPQBOT, namespace=None) -> None:
        self.__opqBot = opqBot
        super().__init__(namespace)

    def on_connect(self):
        self.__opqBot.logger.info(
            '已连接到 OPQBot, 开始获取 QQ: {} 的会话'.format(self.__opqBot.qq))
        self.emit('GetWebConn', self.__opqBot.qq,
                  callback=self.GetWebConnCallBack)  # 取得当前已经登录的QQ链接

    def GetWebConnCallBack(self, data):
        if data == "OK" or data == '当前已存在活动的WebSocket 已为您切换当前Socket':
            self.__opqBot.logger.info('成功')
            self.__opqBot.getFriendAndGroupList()
            self.__opqBot.loadDone(self.__opqBot.qq)
        else:
            self.__opqBot.logger.error(
                '获取 QQ: {} 的会话失败：{}'.format(self.__opqBot.qq, data))

    def on_disconnect(self):
        pass

    def on_OnGroupMsgs(self, payload):
        self.__opqBot.OnGroupMsgs(payload)

    def on_OnFriendMsgs(self, payload):
        self.__opqBot.OnFriendMsgs(payload)

    def on_OnEvents(self, payload):
        self.__opqBot.OnEvents(payload)


pluginInfo = OPQBOT.PluginInfo()
