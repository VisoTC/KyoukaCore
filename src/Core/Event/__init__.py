import collections
from typing import List, Union,Generic,TypeVar
from enum import Enum, unique

EventPayloadBase_T = TypeVar('EventPayloadBase_T')

class EventPayloadBase():
    """
    消息基础类
    """


class ServiceType(Enum):
    Bridge = "Bridge"
    Plugin = "Plugin"
    Core = "Core"


class Eventer(collections.UserString):

    def __init__(self, name: str, t: ServiceType) -> None:
        """
        创建事件对象
        :param name: 名称，Bridge 为登录号码，Plugin 为包名，若为 * 代表全部
        :param t: 类型；Bridge、Plugin、Core
        """
        self._name = name
        self._type = t

    @property
    def data(self):
        return "%s@%s" % (self._name, self._type.value)

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type


class Receiver(collections.UserList):  # 类型标注 [Eventer]

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

    def __init__(self, source: Eventer, terger: Union[Receiver, Eventer], payload: EventPayloadBase) -> None:
        if isinstance(terger, Eventer):
            terger = Receiver(terger)
        self.source = source
        self.terger = terger
        self.payload = payload


class ReceiveEvent(Generic[EventPayloadBase_T]):
    """
    收到的事件
    """

    def __init__(self, source: Eventer, payload: EventPayloadBase_T) -> None:
        self.source = source
        self.payload = payload
