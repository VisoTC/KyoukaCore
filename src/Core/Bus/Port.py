from queue import Queue
from typing import Union
from ..Event import Eventer, SendEvent, ReceiveEvent, EventPayloadBase, Receiver
import logging
import copy


class BusPort():
    def __init__(self, sendBus: Queue, eventer: Eventer) -> None:
        self.logger = logging.getLogger("KyoukaBUSPort: %s" % eventer)
        self._sendPort = sendBus
        self._receivePort: Queue[ReceiveEvent] = Queue()
        self.eventer = eventer

    def send(self, terger: Receiver, payload: EventPayloadBase):
        """
        向消息总线发送消息
        """
        if isinstance(payload, EventPayloadBase):
            self._sendPort.put(
                SendEvent(copy.copy(self.eventer), terger, payload))
        else:
            raise ValueError

    def receive(self, block: bool = True, timeout: Union[float, None] = None):
        """
        接收消息
        """
        return self._receivePort.get(block=block, timeout=timeout)

    def _BUSPort__BUSsend(self, kyoukaMsg: ReceiveEvent):
        if isinstance(kyoukaMsg, ReceiveEvent):
            self._receivePort.put(kyoukaMsg)
        else:
            self.logger.warn("尝试发送非 ReceiveEvent 的事件，抛弃")
