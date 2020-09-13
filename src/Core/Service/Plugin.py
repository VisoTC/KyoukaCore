from typing import Union
from typing import *
from .Service import Service, ServiceInfo, ServiceType, ServiceAPI
from . import ServiceManager
from .exception import ServiceNotReadyException, NotFoundServiceException
from ..Event import EventPayloadBase, Receiver, ReceiveEvent, Eventer
from ..Event.MsgEvent import MsgEvent, MsgContent
from .Bridge import BridgeService
from .UserObj import Users, Groups


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

    @property
    def api(self):
        return self.__api

    @property
    def type(self): return ServiceType.Plugin
