from typing import *
from .Service import Service, ServiceInfo, ServiceType, ServiceAPI
from . import ServiceManager
from .exception import ServiceNotReadyException
from .UserObj import Users, Groups


class BridgeAPI(ServiceAPI):
    __serviceManager = ServiceManager()

    def __init__(self, bridge) -> None:
        self._service: BridgeService
        super().__init__(bridge)

    @property
    def FriendsList(self):
        return self._service.data['FriendsList']

    @property
    def GroupsList(self): return self._service.data['GroupsList']
    
    def updateFriendsList(self, users: Users):
        """
        更新好友列表
        """
        self._service.data['FriendsList'] = users

    def updateGroupsList(self, groups: Groups):
        """
        更新群组列表
        """
        self._service.data['GroupsList'] = groups


class BridgeService(Service):

    def __init__(self, serviceInfo: ServiceInfo):
        super().__init__(serviceInfo)
        self.__api:BridgeAPI = BridgeAPI(self)
        self.data: Dict[str, Any] = {
            'im': "UNKNOW"
        }
    @property
    def api(self):
        return self.__api
    @property
    def type(self): return ServiceType.Bridge

    def initDone(self, uid: str, status: bool, exit: Optional[bool] = None, msg: Optional[str] = None):
        """初始化完成\n调用后会立即触发 register 事件
        :param uid: 操作者使用的 uid
        :param status: 加载是否成功
        :param exit: 加载失败是否退出，默认值退出
        :param msg: 提示信息，默认值：未提供信息"""
        self.eventername = uid
        self.data['im'] = uid
        super().initDone(status, exit, msg)
