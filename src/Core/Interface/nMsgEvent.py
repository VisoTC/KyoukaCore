from enum import Enum, unique
import json


@unique
class MsgEventEnum(Enum):
    UNKNOW = 0                  # 未知事件

    NOTIFY_PUSHADDFRD = 1       # 添加好友成功事件
    FRIEND_ADDED = 2            # 收到好友请求事件
    FRIEND_DELETE = 3           # 被删除好友事件
    FRIEND_REVOKE = 4           # 好友撤回消息事件

    GROUP_JOIN = 11             # 群加入事件
    GROUP_EXIT_SUCC = 12        # 主动退群成功事件
    GROUP_REVOKE = 13           # 群成员撤回消息事件
    GROUP_SHUT = 14             # 群禁言事件
    GROUP_SYSTEMNOTIFY = 15     # 群系统消息事件
    GROUP_ADMIN = 16            # 群管理变更事件
    GROUP_EXIT = 17             # 群成员退出事件
    GROUP_JOIN_SUCC = 18        # 群成员加入事件
    GROUP_ADMINSYSNOTIFY = 19   # 群管理系统消息事件

    MSG_FRIEND = 50            # 好友消息
    MSG_GROUP = 51             # 群消息


class MsgEvent():
    _eventType: MsgEventEnum
    _payload: object

    def __init__(self, eventType, payload) -> None:
        self._eventType = eventType
        self._payload = payload

    @property
    def eventType(self):
        return self._eventType

    @property
    def payload(self):
        return self._payload


class SpecialMsgEventBase(MsgEvent):
    _msgType = MsgEventEnum.UNKNOW

    def __init__(self, payload) -> None:
        super().__init__(self._msgType, payload)

    @property
    def CurrentQQ(self):
        return self._payload['CurrentQQ']


class MSG_FRIEND_EVENT(SpecialMsgEventBase):
    _msgType = MsgEventEnum.MSG_FRIEND

    @property
    def FromUin(self):
        return self._payload['CurrentPacket']['Data']['FromUin']

    @property
    def ToUin(self):
        return self._payload['CurrentPacket']['Data']['ToUin']

    @property
    def MsgType(self):
        return self._payload['CurrentPacket']['Data']['MsgType']

    @property
    def MsgSeq(self):
        return self._payload['CurrentPacket']['Data']['MsgSeq']

    @property
    def Content(self):
        return self._payload['CurrentPacket']['Data']['Content']

    @property
    def RedBaginfo(self):
        return self._payload['CurrentPacket']['Data']['RedBaginfo']

    def __str__(self) -> str:
        return '''私聊:{CurrentQQ}\n{FromUin}:{Content}'''.format(FromUin=self.FromUin, CurrentQQ=self.CurrentQQ, Content=self.Content)


class MSG_GROUP_EVENT(SpecialMsgEventBase):
    _msgType = MsgEventEnum.MSG_GROUP

    @property
    def FromGroupId(self):
        return self._payload['CurrentPacket']['Data']['FromGroupId']

    @property
    def FromGroupName(self):
        return self._payload['CurrentPacket']['Data']['FromGroupName']

    @property
    def FromUserId(self):
        return self._payload['CurrentPacket']['Data']['FromUserId']

    @property
    def FromNickName(self):
        return self._payload['CurrentPacket']['Data']['FromNickName']

    @property
    def Content(self):
        return self._payload['CurrentPacket']['Data']['Content']

    @property
    def MsgType(self):
        return self._payload['CurrentPacket']['Data']['MsgType']

    @property
    def MsgTime(self):
        return self._payload['CurrentPacket']['Data']['MsgTime']

    @property
    def MsgSeq(self):
        return self._payload['CurrentPacket']['Data']['MsgSeq']

    @property
    def MsgRandom(self):
        return self._payload['CurrentPacket']['Data']['MsgRandom']

    @property
    def RedBaginfo(self):
        return self._payload['CurrentPacket']['Data']['RedBaginfo']

    def __str__(self) -> str:
        return '''群:{FromGroupId}@{CurrentQQ}
{FromNickName}({FromUserId}):{Content}'''.format(FromGroupId=self.FromGroupId, CurrentQQ=self.CurrentQQ, FromNickName=self.FromNickName, FromUserId=self.FromUserId, Content=self.Content)


def markMsgEvent(eventType, payload) ->MsgEvent:
    if eventType == MsgEventEnum.MSG_GROUP:
        return MSG_GROUP_EVENT(payload)
    elif eventType == MsgEventEnum.MSG_FRIEND:
        return MSG_FRIEND_EVENT(payload)
    else:
        return MsgEvent(eventType, payload)
