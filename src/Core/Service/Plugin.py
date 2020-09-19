from typing import Union
from typing import *


from ..Event.MsgEvent.MsgContent import TextMsg
from .Service import Service, ServiceInfo, ServiceType, ServiceAPI,Command
from . import ServiceManager
from .exception import ArgsDifferentLengthCommandException, CommandISRegisterException, MatchAndCallException, MatchFailedCommandException, ServiceNotReadyException, NotFoundServiceException
from ..Event import EventPayloadBase, Receiver, ReceiveEvent, Eventer
from ..Event.MsgEvent import MsgEvent, MsgContent
from .Bridge import BridgeService
from .UserObj import Users, Groups
from .msgInfoTypeEnum import MsgInfoTypeEnum



class PluginAPI(ServiceAPI):
    serviceManager = ServiceManager()

    def __init__(self, plugin) -> None:
        super().__init__(plugin)

    def __getService(self, bridgename: Union[Eventer, str]) -> BridgeService:
        if isinstance(bridgename, Eventer):
            bridgename = bridgename.name
        try:
            return self.serviceManager.getService(bridgename, ServiceType.Bridge)
        except KeyError:
            raise NotFoundServiceException

    def getFriendsList(self, bridgename: Union[Eventer, str]):
        """
        获得指定 Bridge 的好友列表
        :param bridgename: 桥的名称
        :return: 列表
        """
        return self.__getService(bridgename).data.get("FriendsList", default=Users())

    def getGroupsList(self, bridgename: Union[Eventer, str]):
        return self.__getService(bridgename).data.get("GroupsList", default=Groups())

    def reply(self, sourceEvent: ReceiveEvent, msgContent: Union[MsgContent, List[MsgContent]], replyMsg=False):
        if not (isinstance(sourceEvent, ReceiveEvent) and isinstance(sourceEvent.payload, MsgEvent) and (isinstance(msgContent, MsgContent) or isinstance(msgContent, list))):
            raise AttributeError
        self.sendMsg(sourceEvent.source, MsgEvent(
            msgInfo=sourceEvent.payload.msgInfo, msgContent=msgContent))


class PluginService(Service):
    def __init__(self, serviceInfo: ServiceInfo):
        super().__init__(serviceInfo)
        self.__api: PluginAPI = PluginAPI(self)
        self._command: Union[Command, None] = None

    @property
    def api(self):
        return self.__api

    @property
    def type(self): return ServiceType.Plugin

    def _receiveMsgEvent(self, event: ReceiveEvent[MsgEvent]):
        if not self._command is None:
            if not event.payload.getFirstMsgContent() is None:
                content = event.payload.getFirstMsgContent()
                # 如果最开头是纯文本消息，判断是不是/开头的，/开头视作命令
                if isinstance(content, TextMsg):
                    if content.content[0] == "/":
                        try:
                            self._command.matchAndCall(
                                content.content[1:], event)
                        except MatchAndCallException as e:
                            if e.type == ArgsDifferentLengthCommandException:
                                if len(self._registerCalls.get("ArgsError@command", [])) == 0:
                                    self._commandArgsError(event, e)
                                else:
                                    for call in self._registerCalls.get("ArgsError@command"):
                                        call(event, e)
                            elif e.type == MatchFailedCommandException:
                                if len(self._registerCalls.get("NotFound@command", [])) == 0:
                                    self._commandNotFound(event, e)
                                else:
                                    for call in self._registerCalls.get("NotFound@command"):
                                        call(event, e)
                        except MatchFailedCommandException:  # 不是自己的命令
                            pass
                    else:
                        super()._receiveMsgEvent(event)

    def _commandArgsError(self, event:ReceiveEvent[MsgEvent], e):
        com = []
        for i in e.trace[::-1]:
            com.append(i.command)
        com = " ".join(com)
        msg = "命令：/{} 参数不匹配\n参数：/{} {}".format(com,
                                               com, e.trace[0].func.argsText)
        self.api.reply(event, TextMsg(msg))

    def _commandNotFound(self, event:ReceiveEvent[MsgEvent], e):
        com = []
        for i in e.trace[::-1]:
            com.append(i.command)
        com = " ".join(com)
        subCom = []
        for i in e.trace[0].subs:
            if not MsgInfoTypeEnum.msgInfo2Enum(type(event.payload.msgInfo)).value in i.msgtypes : # 跳过不匹配当前
                continue
            subCom.append("/" + com + " " + i.command +
                          ((" " + i.func.argsText)if i.func != None else "") + ": " + i.doc)
        msg = "匹配不到命令\n- /{} - {}\n—————\n可用的下属命令\n{}".format(
            com, e.trace[0].doc, '\n'.join(subCom))
        self.api.reply(event, TextMsg(msg))

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
