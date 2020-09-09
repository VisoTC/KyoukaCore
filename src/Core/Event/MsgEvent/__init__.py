from .. import EventPayloadBase
from .MsgInfo import MsgInfo
from .MsgContent import MsgContent
from typing import List, Union


class MsgEvent(EventPayloadBase):
    def __init__(self, msgInfo: MsgInfo, msgContent: Union[MsgContent, List[MsgContent]]) -> None:
        """
        事件消息
        :param bridge: 事件产生的 Bridge 信息
        :param msgInfo: 事件信息
        :param msgContent: 事件内容(消息链)
        """
        self.msgInfo = msgInfo
        if not isinstance(msgContent, list):
            self.msgContent = [msgContent]
        else:
            self.msgContent = msgContent

    def getFirstMsgContent(self) -> Union[MsgContent, None]:
        """获得 msgContent 的第一条消息"""
        if len(self.msgContent) > 0:
            return self.msgContent[0]
        else:
            return None
