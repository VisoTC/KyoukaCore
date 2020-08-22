from Core.Interface.IPlugin import IPlugin
from Core.Interface.IBridge import IBridge
#from . import KyoukaCore
from .Interface.Msg.MsgInfo import MsgInfo
from .Interface.Msg.MsgInfo import GroupMsgInfo
from .Exception import *
from Core.Interface.UserObj import User, Users, Group, Groups


class KyoukaAPI():
    """
    提供核心交互的 API
    """

    def __init__(self, Core) -> None:
        """
        初始化 API
        """
        self.__core = Core

    @property
    def adminUser(self, bridgeName):
        """
        返回管理员的账户ID
        :param bridgeName: 操作的桥的名字
        """
        self.__core.config['adminUser']

    @property
    def isAdminUser(self, bridgeName,msgInfo: MsgInfo) -> bool:
        """
        判断是否是管理员账户
        :param bridgeName: 操作的桥的名字
        :param msgInfo: 消息对象信息
        :raise KyoukaAPIValueException: msgInfo 类型错误
        """
        if isinstance(msgInfo, MsgInfo):
            if isinstance(msgInfo, GroupMsgInfo):
                return msgInfo.UserId == self.getAdminUser
            return False
        else:
            raise KyoukaAPIValueException
    
    def allBridgeName(self):
        return self.__core.bridgeInfo.keys()
    
    def allBridge(self):
        return self.__core.bridgeInfo


    def friendsList(self, bridgeName)-> Users:
        """
        获得好友列表:
        :param bridgeName: 操作的桥的名字
        :return: 好友列表对象
        :raise BridgeNotFoundException: bridge 名称错误
        """
        bridge:IBridge = self.__core.bridgeInfo.get(str(bridgeName))
        if bridge == None:
            raise BridgeNotFoundException
        return bridge.UserList

    def groupList(self, bridgeName) -> Groups:
        """
        获得群组列表:
        :param bridgeName: 操作的桥的名字
        :return: 群组列表
        :raise BridgeNotFoundException: bridge 名称错误
        """
        bridge:IBridge = self.__core.bridgeInfo.get(str(bridgeName))
        if bridge == None:
            raise BridgeNotFoundException
        return bridge.GroupList


class KyoukaBridgeAPI(KyoukaAPI):
    def _init(self, bridge:IBridge):
        self.__bridge = bridge
        self.__bridgeName = bridge.msgBusPort.name

    def friendsList(self):
        """
        获得当前桥绑定的好友列表:
        :return: 好友列表
        """
        return self.__bridge._IBridge__UserList

    def gruopList(self):
        """
        获得当前桥绑定的群组列表:
        :return: 群组列表
        """
        return self.__bridge._IBridge__GroupList
