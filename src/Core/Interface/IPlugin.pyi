from Core.MsgBus import MsgBusPort
from abc import ABCMeta

import threading
from Core.API import KyoukaAPI
from Core.Config import ConfigFactory
from Core.Logger import LogSerivce


class IPlugin(threading.Thread, metaclass=ABCMeta):
    def __init__(self, msgBusPort: MsgBusPort, configRoot: ConfigFactory,
                 logSerivce: LogSerivce, KyoukaAPI: KyoukaAPI) -> None: ...
    ...
