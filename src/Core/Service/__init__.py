import logging
from tkinter.constants import N
from typing import *
import threading
import enum
from abc import ABCMeta, abstractmethod

from .Command import Command

from ..Event.MsgEvent.MsgContent import TextMsg
from ..Event.MsgEvent import MsgEvent

from ..Bus.Port import BusPort
from ..Event.MsgEvent.MsgInfo import MsgInfo, GroupMsgInfo, GroupPrivateMsgInfo, PrivateMsgInfo
from ..utlis import ReadOnly

from ..Bus import Bus


class ServiceInfo(ReadOnly):
    """
    服务属性
    """

    def __init__(self, packageName: str, name: str, version: str, author: str) -> None:
        self.packageName = packageName
        self.name = name
        self.version = version
        self.author = author
        self._readOnlyLock()


class MsgInfoTypeEnum(enum.Enum):
    GroupMsg = 'GroupMsg'
    GroupPrivateMsg = 'GroupPrivateMsg'
    PrivateMsg = 'PrivateEvent'

    GroupEvent = 'GroupEvent'
    GroupPrivateEvent = 'GroupPrivateEvent'
    PrivateEvent = 'PrivateEvent'

    @classmethod
    def value(cls, msgInfo: MsgInfo):
        if type(msgInfo) == type(GroupMsgInfo):
            return cls.GroupMsg
        elif type(msgInfo) == type(GroupPrivateMsgInfo):
            return cls.GroupPrivateMsg
        else:
            raise ValueError


class Service(metaclass=ABCMeta):
    """
    Plugin 与 Bridge 的底层类以及通用方法
    """

    @property
    @abstractmethod
    def type(cls): return "Service"

    def __init__(self, serviceInfo: ServiceInfo) -> None:
        self._serviceInfo = serviceInfo
        self._ready = False
        self._busPort: Union[BusPort, None] = None
        self._registerCalls: Dict[MsgInfoTypeEnum, list] = {}
        self._command:Union[Command,None] = None
        self.logger = logging.getLogger(
            "%s@%s" % (self._serviceInfo.name, self.type))

    @property
    def info(self) -> ServiceInfo:
        """
        返回信息
        """
        return self._serviceInfo

    def _receiveEventThread(self):
        """
        接收消息线程
        """
        while not self._busPort is None:
            event = self._busPort.receive()
            if isinstance(event.payload, MsgEvent):
                if not self._command is None:
                    if not event.payload.getFirstMsgContent() is None:
                        content = event.payload.getFirstMsgContent()
                        if isinstance(content, TextMsg):
                            if content.content[0] == "/":
                                self._command.matchAndCall(content.content[1:])
                                continue
                if MsgInfoTypeEnum.value(event.payload.msgInfo) in self._registerCalls.keys():
                    for call in self._registerCalls.get(MsgInfoTypeEnum.value(event.payload.msgInfo)):
                        try:
                            call(event)
                        except Exception as e:
                            self.logger.exception(e)


class ServiceManager():
    """
    负责管理所有的 Service 类，单例
    """
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not hasattr(ServiceManager, "_instance"):
            with ServiceManager._instance_lock:
                if not hasattr(ServiceManager, "_instance"):
                    ServiceManager._instance = super(
                        ServiceManager, cls).__new__(cls)
        return ServiceManager._instance

    def __init__(self) -> None:
        self._ServerList: List[Service] = []
        self._bus = Bus()

    def append(self, item: Service) -> None:
        if isinstance(item, Service):
            self._ServerList.append(item)
        else:
            raise ValueError

    def register(self, service: Service):
        """
        注册服务，并分配消息总线及启动监听
        """
