from Core.Event import CoreEvent
from .Service import Service
from typing import *
import threading
from ..Event import Eventer, ServiceType, CoreEvent
from ..Bus import Bus
from ..Config import ConfigFactory

class ServiceList():

    def __init__(self) -> None:
        self.data = {
            ServiceType.Bridge: {},
            ServiceType.Plugin: {},
            ServiceType.Core: {},
        }

    @property
    def Bridge(self) -> Dict[str, Service]:
        return self.data[ServiceType.Bridge]

    @property
    def Plugin(self) -> Dict[str, Service]:
        return self.data[ServiceType.Plugin]

    @property
    def Core(self) -> Dict[str, Service]:
        return self.data[ServiceType.Core]


class ServiceManager():
    """
    负责管理所有的 Service 类，单例
    """
    coreEvent = {
        "register": CoreEvent.Register()
    }
    _instance_lock = threading.Lock()
    __isInit = False

    def __new__(cls, *args, **kwargs):
        if not hasattr(ServiceManager, "_instance"):
            with ServiceManager._instance_lock:
                if not hasattr(ServiceManager, "_instance"):
                    ServiceManager._instance = super(
                        ServiceManager, cls).__new__(cls)
        return ServiceManager._instance

    def __init__(self) -> None:
        if not self.__isInit:
            self._ServerList: List[Service] = []
            self.serivces = ServiceList()
            self._bus = Bus()
            self._serviceManagerPort = self._bus.getBusPort(
                Eventer("ServiceManager", ServiceType.Core))
            self.__isInit = True
            

    def getService(self, name: str, type: ServiceType) -> Any:
        if type == ServiceType.Bridge:
            return self.serivces.Bridge[name]
        elif type == ServiceType.Plugin:
            return self.serivces.Plugin[name]
        elif type == ServiceType.Core:
            return self.serivces.Core[name]
        else:
            raise KeyError

    def _append(self, item: Service) -> None:
        if isinstance(item, Service):
            if item.type == ServiceType.Bridge:
                if not item.eventername in self.serivces.Bridge.keys():
                    self.serivces.Bridge[item.eventername] = item
                    return
            elif item.type == ServiceType.Plugin:
                if not item.eventername in self.serivces.Plugin.keys():
                    self.serivces.Plugin[item.eventername] = item
                    return
            elif item.type == ServiceType.Core:
                if not item.eventername in self.serivces.Core.keys():
                    self.serivces.Core[item.eventername] = item
                    return
            else:
                raise ValueError
            raise IndexError
        else:
            raise ValueError

    def register(self, service: Service):
        """
        注册服务，并分配消息总线及创建监听对象
        """
        self._append(service)
        service._busPort = self._bus.getBusPort(
            Eventer(service.eventername, service.type))
        self._serviceManagerPort.send(
            Eventer(service.eventername, service.type), self.coreEvent['register'])
    
    def wait(self):
        self._bus.wait()
