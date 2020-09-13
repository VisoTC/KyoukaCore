from datetime import time
import unittest
from Core.Event import ReceiveEvent, Eventer, ServiceType, EventPayloadBase
from Core.Service import ServiceManager
from Core.Service.Plugin import PluginService, ServiceInfo
from Core.Service.Bridge import BridgeService
from Core.Service.exception import *

from time import sleep


class testService(unittest.TestCase):

    def setUp(self) -> None:
        self.serviceManager = ServiceManager()
        self.plugin = PluginService(ServiceInfo(**{
            'packageName': "com.visotc.KyoukaCore.ExamplePlugin",
            'name': "测试插件",
            'version': "dev",
            'author': "VisoTC"
        }))
        self.bridge = BridgeService(ServiceInfo(**{
            'packageName': "com.visotc.KyoukaCore.ExamplePlugin",
            'name': "测试插件",
            'version': "dev",
            'author': "VisoTC"
        }))
        self._data = None

    pluginData = ""

    bridgeData = ""

    def test_正常测试(self):
        # 测试注册事件
        @self.bridge.register("register")
        def _(event):
            self.bridgeData = "bridge register"

        def plugin_register(event):
            self.pluginData = "plugin register"

        self.plugin.register("register", plugin_register)
        
        self.plugin.initDone()
        self.bridge.initDone('testqq')

        self.assertEqual(
            self.serviceManager.serivces.Plugin['com.visotc.KyoukaCore.ExamplePlugin'], self.plugin)
        self.assertEqual(
            self.serviceManager.serivces.Bridge['testqq'], self.bridge)

        sleep(0.1)
        self.assertEqual(
            "bridge register", self.bridgeData)
        self.assertEqual(
            "plugin register", self.pluginData)
