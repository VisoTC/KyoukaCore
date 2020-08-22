from abc import ABCMeta
from .IPlugin import IPlugin
from Core.Interface.UserObj import User, Users, Group, Groups


class IBridge(IPlugin, metaclass=ABCMeta):
    def _IPlugin__setlogger(self):
        """
        设定 Logger 的名称
        """
        self._IPlugin__logger = self._IPlugin__LogSerivce.getLogger(
            "{name}@bridge".format(name=self.pluginInfo['name']))

    def _IBridge__init(self):
        self._IBridge__UserList = Users()
        self._IBridge__GroupList = Groups()

    def loadDone(self, name):
        self.msgBusPort.name = name
        self._IPlugin__loadReady.set()

    @property
    def UserList(self):
        return self._IBridge__UserList

    @property
    def GroupList(self):
        return self._IBridge__GroupList
    
