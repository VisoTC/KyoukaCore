from enum import Enum
from typing import Type

from ..Event.MsgEvent.MsgInfo import MsgInfo,GroupMsgInfo,GroupPrivateMsgInfo,PrivateMsgInfo
class MsgInfoTypeEnum(Enum):
    GroupMsg = 'GroupMsg'
    GroupPrivateMsg = 'GroupPrivateMsg'
    PrivateMsg = 'PrivateEvent'

    GroupEvent = 'GroupEvent'
    GroupPrivateEvent = 'GroupPrivateEvent'
    PrivateEvent = 'PrivateEvent'

    @classmethod
    def msgInfo2Enum(cls, msgInfo: Type[MsgInfo]):
        if msgInfo == GroupMsgInfo:
            return cls.GroupMsg
        elif msgInfo == GroupPrivateMsgInfo:
            return cls.GroupPrivateMsg
        elif msgInfo == PrivateMsgInfo:
            return cls.PrivateMsg
        else:
            raise ValueError