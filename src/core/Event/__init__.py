import collections
from typing import List, Union
from enum import Enum


class EventPayloadBase():
    """
    消息基础类
    """


EventerType = Enum("EventerType", "Bridge Plugin Core")


class Eventer(collections.UserString):

    def __init__(self, name: str, t: EventerType) -> None:
        """
        创建事件对象
        :param name: 名称，Bridge 为登录号码，Plugin 为包名，若为 * 代表全部
        :param t: 类型；Bridge、Plugin、Core
        """
        self._name = name
        self._type = t

    @property
    def data(self):
        return "%s@%s" %(self._name,self._type)

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type


class Receiver(collections.UserList[Union[Eventer]]):

    def __init__(self, receiver: Union[Eventer, List[Eventer]]) -> None:
        """
        接收者列表
        :param eventer:接收者列表
        """
        if isinstance(receiver, list):
            super().__init__(receiver)
        else:
            super().__init__([receiver])


class KyoukaMsgs():
    """
    消息包裹，包含了发送者，接收者和载荷
    """

    def __init__(self, source: Eventer, terger: Receiver, payload: EventPayloadBase) -> None:
        self.source = source
        self.terger = terger
        self.payload = payload


class SendEvent():
    """
    发送的事件
    """

    def __init__(self, source: Eventer, terger: Receiver, payload: EventPayloadBase) -> None:
        self.source = source
        self.terger = terger
        self.payload = payload


class ReceiveEvent():
    """
    收到的事件
    """

    def __init__(self, source: Eventer, payload: EventPayloadBase) -> None:
        self.source = source
        self.payload = payload
