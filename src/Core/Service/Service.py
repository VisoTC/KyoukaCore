import inspect
import logging
from threading import Thread
from typing import *
import threading
from abc import ABCMeta, abstractmethod
from enum import Enum

from ..Event.CoreEvent import KyoukaCoreEventBase, Register

from ..Event.MsgEvent.MsgInfo import MsgInfo, GroupMsgInfo, GroupPrivateMsgInfo, PrivateMsgInfo

from ..Event import EventPayloadBase, Eventer, ServiceType, ReceiveEvent, Receiver
from ..utlis import ReadOnly
from ..Config import Config

from .Command import Command, FuncAttr

from ..Event.MsgEvent.MsgContent import TextMsg
from ..Event.MsgEvent import MsgEvent

from ..Bus.Port import BusPort

from .exception import ServiceNotReadyException, ServiceRegisterFailerException, MatchAndCallException, ArgsDifferentLengthCommandException, MatchFailedCommandException
from .exception import MustOneArgsCommandException, CommandISRegisterException


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


class ServiceReady():
    def __init__(self) -> None:
        self.__flag = threading.Event()
        self.reset()

    @property
    def isUpdata(self):
        return self.__flag.is_set()

    def wait(self, timeout=None):
        if self.__flag.wait(timeout=timeout):
            return self.__status, self.__exit, self.__msg

    def updata(self, status: bool, e: Optional[bool] = True, msg: Optional[str] = None):
        self.__status = status
        if status:
            self.__flag.set()
        if e is None:
            e = True
        self.__exit = e
        if not msg is None:
            self.__msg = msg

    def reset(self):
        self.__flag.clear()
        self.__status = False
        self.__exit = True
        self.__msg = "未提供信息"


class ServiceAPI():

    def __init__(self, service) -> None:
        self._service: Service = service

    def sendMsg(self, terger: Union[Receiver, Eventer], payload: EventPayloadBase):
        if self._service.ready:
            self._service._busPort.send(terger, payload)
        else:
            raise ServiceNotReadyException


class Service(metaclass=ABCMeta):
    """
    Plugin 与 Bridge 的底层类以及通用方法
    """

    @property
    @abstractmethod
    def type(cls): return ServiceType.Core

    @property
    def ready(self):
        return self.__ready.isUpdata

    def __init__(self, serviceInfo: ServiceInfo) -> None:
        from . import ServiceManager
        self._serviceInfo = serviceInfo
        self._serviceManager = ServiceManager()

        self._thread: threading.Thread = threading.Thread(
            target=self._receiveEventThread, daemon=True, name="[receive]" + self.info.packageName)
        self._mainThread: Optional[Union[Thread]] = None
        self.logger = logging.getLogger(
            "%s@%s" % (self._serviceInfo.name, self.type.value))

        self.__config = Config(self._serviceInfo.packageName)

        self.__ready = ServiceReady()

        self._busPort: Union[BusPort, None] = None
        self._registerCalls: Dict[Union[MsgInfoTypeEnum,
                                        str], List[Callable]] = {}
        self._command: Union[Command, None] = None

        self.eventername = self._serviceInfo.packageName

        self.logger.info("开始载入：%s" % self.info.name)

    @property
    def config(self) -> Config:
        return self.__config

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
        self.logger.info("初始化完成，开始运行消息循环")
        while not self._busPort is None:
            event = self._busPort.receive()
            # 如果是消息事件
            if isinstance(event.payload, MsgEvent):
                # 如果最开头是纯文本消息，判断是不是/开头的，/开头视作命令
                if not self._command is None:
                    if not event.payload.getFirstMsgContent() is None:
                        content = event.payload.getFirstMsgContent()
                        if isinstance(content, TextMsg):
                            if content.content[0] == "/":
                                try:
                                    self._command.matchAndCall(
                                        content.content[1:], event)
                                except MatchAndCallException as e:
                                    if e.type == ArgsDifferentLengthCommandException:
                                        for call in self._registerCalls.get("ArgsError@command"):
                                            call(e)
                                    elif e.type == MatchFailedCommandException:
                                        for call in self._registerCalls.get("NotFound@command"):
                                            call(e)

                                continue
                # 将非命令消息发送给绑定的消息
                if MsgInfoTypeEnum.msgInfo2Enum(type(event.payload.msgInfo)).value in self._registerCalls.keys():
                    for call in self._registerCalls.get(MsgInfoTypeEnum.msgInfo2Enum(type(event.payload.msgInfo)).value, []):
                        try:
                            call(event)
                        except Exception as e:
                            self.logger.exception(e)
            # KyoukaCore 事件
            elif isinstance(event.payload, KyoukaCoreEventBase):
                if isinstance(event.payload, Register):
                    for call in self._registerCalls.get("register", []):
                        self._mainThread = threading.Thread(
                            target=call, args=[event], name=self.info.packageName)
                        self._mainThread.start()
        self.logger.error("消息循环异常退出，此插件已退出")
        self.__ready.reset()

    def initDone(self, status: bool = True, e: Optional[bool] = None, msg: Optional[str] = None):
        """初始化完成\n
        调用后会立即触发 register 事件
        :param status: 加载是否成功
        :param e: 加载失败是否退出，默认值退出
        :param msg: 提示信息，默认值：未提供信息"""
        self.__ready.updata(status, e, msg)
        if self.__ready.isUpdata and status:
            self._serviceManager.register(self)
            if isinstance(self._busPort, BusPort):
                self._thread.start()
                return
        if msg is None:
            msg = "未提供信息"
        if not status:
            if e:
                text = "载入时发生致命错误：{}"
            else:
                text = "载入时发生错误，将跳过载入：{}"
            self.logger.error(text.format(msg))
            if e:
                exit()

    def register(self, callbackName: Union[Type[MsgInfo], str], func: Optional[Callable[[ReceiveEvent], Any]] = None):
        """
        注册一个消息回调
        :param callbackName: 回调名称
        :param func: [非装饰器模式需要]调用的参数（必须只有一个参数）
        :raise MustOneArgsCommandException: 必须只能有一个参数
        :raise AttributeError: 没有 func 参数
        """
        if func is None:
            def wrapper(func):
                self.__register(callbackName, func)
                return func

            return wrapper
        else:
            self.__register(callbackName, func)

    def __register(self, callbackName: Union[Type[MsgInfo], str], func: Callable):
        """
        注册一个消息回调
        :param msgInfo: 回调名称
        :param func: 调用的参数（必须只有一个参数）
        :raise MustOneArgsCommandException: 必须只能有一个参数
        """
        if func is None:
            raise AttributeError
        if not isinstance(callbackName, str):
            cName: str = MsgInfoTypeEnum.msgInfo2Enum(callbackName).value
        else:
            cName = callbackName
        if len(inspect.signature(func).parameters.keys()) != 1:
            raise MustOneArgsCommandException
        if not callbackName in self._registerCalls.keys():
            self._registerCalls[cName] = []
        self._registerCalls[cName].append(func)

    def registerCommand(self, command: Command):
        """
        注册一个命令对象
        :param command: 命令对象
        :raise CommandISRegisterException: 命令对象已经存在
        """
        if self._command is None:
            self._command = command
        else:
            raise CommandISRegisterException
