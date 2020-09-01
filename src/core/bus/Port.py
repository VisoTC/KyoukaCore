from queue import Queue
from ..Event import Eventer, SendEvent, ReceiveEvent, EventPayloadBase, Receiver
import logging,copy


class BUSPort():
    def __init__(self, sendBus: Queue, eventer: Eventer) -> None:
        self.logger = logging.getLogger("KyoukaBUSPort: %s" % eventer)
        self._sendPort = sendBus
        self._receivePort: Queue[ReceiveEvent] = Queue()
        self.eventer = eventer
    
    def send(self, terger: Receiver, payload: EventPayloadBase):
        """
        向消息总线发送消息
        """
        self._sendPort.put(SendEvent(copy.copy(self.eventer), terger, payload))

    def receive(self):
        """
        接收消息
        """
        return self._receivePort.get()

    def _BUSPort__BUSsend(self, kyoukaMsg: ReceiveEvent):
        if isinstance(kyoukaMsg, ReceiveEvent):
            self._receivePort.put(kyoukaMsg)
        else:
            self.logger.warn("尝试发送非 ReceiveEvent 的事件，抛弃")
