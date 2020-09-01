from queue import Queue
from .Port import BUSPort
from typing import Dict, List
from ..Event import Eventer, EventerType, ReceiveEvent, SendEvent
import threading


class BUS():
    """
    消息总线
    """

    def __init__(self) -> None:
        self._sendBus: Queue[SendEvent] = Queue()  # 发送总线

        self._ports: Dict[EventerType, List[BUSPort]] = {
            EventerType.Plugin: [],
            EventerType.Bridge: [],
            EventerType.Core: []
        }
        BUSThread = threading.Thread(
            target=self.threadMain, name="KyoukaCore event BUS loop thread",daemon=True)
        BUSThread.start()

    def threadMain(self):
        while True:
            kyoukaMsg = self._sendBus.get(block=True)  # 从发送总线中获取事件
            for terger in kyoukaMsg.terger:  # 判断事件接收者类型
                for port in self._ports[terger.type]:  # 获得接收者端口
                    if terger.name == "*" or terger.name == port.eventer.name:  # 判断是否符合，不符合就跳过
                        port._BUSPort__BUSsend(ReceiveEvent(
                            kyoukaMsg.source, kyoukaMsg.payload))  # 重新组装成为接收者事件并发送事件
                    else:
                        continue

    def getBusPort(self, eventer: Eventer):
        busPort = BUSPort(self._sendBus, eventer)
        self._ports[busPort.eventer.type].append(busPort)
        return busPort
