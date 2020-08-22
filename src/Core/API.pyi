from Core.Interface.IPlugin import IPlugin
from Core.Interface.IBridge import IBridge
from . import KyoukaCore
from .Interface.Msg.MsgInfo import MsgInfo
from .Interface.Msg.MsgInfo import GroupMsgInfo
from .Exception import *
from Core.Interface.UserObj import User, Users, Group, Groups


class KyoukaAPI():
    """
    提供核心交互的 API
    """

    def __init__(self, Core:KyoukaCore) -> None:
        """
        初始化 API
        """
        self.__core = Core