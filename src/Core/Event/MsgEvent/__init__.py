from .. import EventPayloadBase
from .MsgInfo import MsgInfo
from .MsgContent import MsgContent
from typing import Dict, List, Optional, Union, Any


class MsgEvent(EventPayloadBase):
    def __init__(self, msgInfo: MsgInfo, msgContent: Union[MsgContent, List[MsgContent]], otherData: Optional[Dict[str, Any]] = None) -> None:
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
        if otherData is None:
            otherData = {}
        self.otherData = otherData

    def getFirstMsgContent(self) -> Union[MsgContent, None]:
        """获得 msgContent 的消息链的第一条"""
        if len(self.msgContent) > 0:
            return self.msgContent[0]
        else:
            return None
