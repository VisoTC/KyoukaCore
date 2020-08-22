from .MsgInfo import MsgInfo
from .MsgContent import MsgContent
from typing import List, Union


class MsgBase():
    def __init__(self, bridge: str, time: int) -> None:
        """
        事件消息基础类
        :param Bridge: 事件产生的 Bridge 信息
        :param Time: 消息时间
        """
        self.bridge = bridge  # None 的将由 Port 负责填写
        self.bridge = bridge


class MsgEvent(MsgBase):
    def __init__(self, bridge: str, time: int, msgInfo: MsgInfo, msgContent: Union[List[MsgContent], MsgContent]) -> None:
        """
        事件消息
        :param bridge: 事件产生的 Bridge 信息
        :param Time: 事件时间
        :param msgInfo: 事件信息
        :param msgContent: 事件内容
        """
        super().__init__(bridge, time)
        self.msgInfo = msgInfo
        if not isinstance(msgContent, list):
            self.msgContent = [msgContent]
        else:
            self.msgContent = msgContent
