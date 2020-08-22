from asyncio.events import AbstractEventLoop
from .Interface.Msg.MsgInfo import GroupMsgInfo
from .Interface.Msg.MsgBase import MsgEvent
from asyncio import Queue
import asyncio
from logging import Logger, debug
#from Core.Logger import LogSerivce
import threading
from .Interface.Msg.MsgBase import MsgBase


class SetMsgPortNameException(Exception):
    ...


class NotSupportPayloadException(Exception):
    ...


class MsgBusPort():
    def __init__(self, sendBus: Queue, t: str, l) -> None:
        self._sendPort = sendBus
        self._receivePort = Queue()
        self.name = None
        self._t = t
        self.__loop = l

    async def _sendAsync(self, payload):
        self.checkName()
        if isinstance(payload, MsgBase):
            self._bulidMsg(payload)
        else:
            raise NotSupportPayloadException
        await self._sendPort.put(payload)

    async def _receiveAsync(self):
        self.checkName()
        a = await self._receivePort.get()
        return a

    def send(self, payload:MsgEvent):
        '''
        将载荷发送到消息总线
        :param payload: 载荷
        '''
        self.checkName()
        if isinstance(payload, MsgBase):
            self._bulidMsg(payload)
        else:
            raise NotSupportPayloadException
        a = asyncio.run_coroutine_threadsafe(
            self._sendAsync(payload), loop=self.__loop)
        return a.result()

    def receive(self) -> MsgEvent:
        '''
        从消息总线获得载荷，同步版本
        :return 载荷
        '''
        self.checkName()
        a = asyncio.run_coroutine_threadsafe(
            self._receiveAsync(), loop=self.__loop)
        return a.result()

    def checkName(self):
        if self.name is None:
            raise SetMsgPortNameException

    def _bulidMsg(self, msg: MsgBase):
        if msg.bridge is None and not self.name is None:
            msg.bridge = self.name


class MsgBus():
    """
    消息总线
    """
    

    def __init__(self,logger:Logger,asyncLoop:AbstractEventLoop) -> None:
        self.logger = logger
        self._loop = asyncLoop  # 创建消息循环
        #asyncio.set_event_loop(self._loop)

        #self._t = threading.Thread(target=self.start_loop)  # 在新线程以协程方式转发消息
        #self._t.name = "Msg Forward Bus Loop"
        #self._t.start()

        self._bridgeSendBus = Queue()  # Bridge 公用发送总线
        self._pluginSendBus = Queue()  # plugin 公用发送总线
        self._coreSendBus = Queue()  # Core 公用发送总线

        self._bridgePorts = []  # Bridge 的消息端口
        self._pluginPorts = []  # Plugin 的消息端口

        asyncio.run_coroutine_threadsafe(self.pluginForward(), self._loop)
        asyncio.run_coroutine_threadsafe(self.bridgeForward(), self._loop)

    def CoreBusCallback(self,fun):
        asyncio.run_coroutine_threadsafe(fun(), self._loop)

    def getPort(self, role):
        """
        创建一个总线端口

        :param role: 申请者角色（Brdge、Plugin）
        """

        if role == "Plugin":
            msgBusPort = MsgBusPort(self._pluginSendBus, "Plugin",self._loop)
            self._pluginPorts.append(msgBusPort)
        elif role == "Bridge":
            msgBusPort = MsgBusPort(self._bridgeSendBus, "Bridge",self._loop)
            self._bridgePorts.append(msgBusPort)
        elif role == "Core":
            msgBusPort = MsgBusPort(self._bridgeSendBus, "Core",self._loop)
            self._bridgePorts.append(msgBusPort)
        else:
            raise Exception
        return msgBusPort

    async def pluginForward(self):
        self.logger.debug("Plugin 事件开始转发到 Bridge")
        while True:
            msg = await self._pluginSendBus.get()
            self.logger.debug("Forward to bridge msg")
            for port in self._bridgePorts:
                await port._receivePort.put(msg)
            

    async def bridgeForward(self):
        self.logger.debug("Bridge 事件开始转发到 Plugin")
        while True:
            msg = await self._bridgeSendBus.get()
            self.logger.debug("Forward to plugin msg")
            for port in self._pluginPorts:
                await port._receivePort.put(msg)


    def getloop(self):
        return self._loop
