from queue import Queue
from .Port import BusPort
from typing import Dict, List
from ..Event import Eventer, ServiceType, ReceiveEvent, SendEvent
import threading
import ctypes

from fnmatch import fnmatch


class Bus():
    """
    消息总线
    """

    def __init__(self) -> None:
        self._sendBus: Queue[SendEvent] = Queue()  # 发送总线

        self._ports: Dict[ServiceType, List[BusPort]] = {
            ServiceType.Plugin: [],
            ServiceType.Bridge: [],
            ServiceType.Core: []
        }
        self.__BUSThread = threading.Thread(
            target=self.threadMain, name="KyoukaCore event BUS loop thread", daemon=True)
        self.__BUSThread.start()

    def wait(self):
        self.__BUSThread.join()

    def threadMain(self):
        while True:
            kyoukaMsg = self._sendBus.get(block=True)  # 从发送总线中获取事件
            for terger in kyoukaMsg.terger:  # 判断事件接收者类型
                for port in self._ports[terger.type]:  # 获得接收者端口
                    if fnmatch(port.eventer.name, terger.name):  # 判断是否符合，不符合就跳过
                        port._BUSPort__BUSsend(ReceiveEvent(
                            kyoukaMsg.source, kyoukaMsg.payload))  # 重新组装成为接收者事件并发送事件
                    else:
                        continue

    def getBusPort(self, eventer: Eventer):
        busPort = BusPort(self._sendBus, eventer)
        self._ports[busPort.eventer.type].append(busPort)
        return busPort

    def close(self):
        if not self.__BUSThread.ident is None:
            tid = self.__BUSThread.ident
        else:
            raise ValueError("invalid thread id")
        
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(tid), ctypes.py_object(SystemExit))
        
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                self.__BUSThread.ident, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
        else:
            pass

    def __del__(self):
        self.close()
