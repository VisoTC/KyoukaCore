# 机器人核心类，在主线程上运行
from Core.Interface.IPlugin import IPlugin
from Core import Interface
import asyncio
import threading

from .API import KyoukaAPI
from .Config import ConfigFactory, Config
from .Logger import LogSerivce


from .Interface.IBridge import IBridge
from .MsgBus import MsgBus

from Plugin import PCR, setu, GuildWarQuery
from Bridge import OPQBOT

from typing import Dict


class KyoukaCore():
    bridgeThread: Dict[str, IBridge] = {}

    def __init__(self) -> None:
        self.bridgeInfo = {}
        pass

    def run(self):
        # load Logging
        self.logSerivce = LogSerivce()
        self.logger = self.logSerivce.getCoreLogger()

        self.logger.info("KyoukaCore 开始启动...")
        self.KyoukaAPI = KyoukaAPI(self)
        # load Config
        self.logger.info("载入配置文件...")
        self.configRoot = ConfigFactory(self.logger)
        self.config = Config(self.configRoot, "KyoukaBot")

        # init async
        self.asyncInit()

        # load Queue
        self.msgBus = MsgBus(self.logger, self._loop)
        # load Core 事件监听，必须在消息总线初始化之后才可调用
        asyncio.run_coroutine_threadsafe(self.coreMonitor(), self._loop)

        # load Brdge
        # TODO: 下次一定实现动态寻找载入插件
        '''
        self.logger.info("Loading Kyouka bridge")
        bridge = OPQBOT.pluginInfo['entrance']
        bridge = bridge(msgBusPort=self.msgBus.getPort("Bridge"),
                        configRoot=self.configRoot, logSerivce=self.logSerivce, KyoukaAPI=self.KyoukaAPI)
        bridge.start()
        # load plugin
        self.logger.info("Loading Kyouka plugin")
        plugin = PCR.pluginInfo['entrance']
        plugin = plugin(msgBusPort=self.msgBus.getPort("Plugin"),
                        configRoot=self.configRoot, logSerivce=self.logSerivce, KyoukaAPI=self.KyoukaAPI)
        plugin.start()
        '''
        if not self.config.get('DisablePlugin', False):
            self.config['DisablePlugin'] = []
            self.config.commit()
        self.loadPlugin(OPQBOT, "Bridge")
        self.loadPlugin(PCR, "Plugin")
        self.loadPlugin(setu, "Plugin")
        self.loadPlugin(GuildWarQuery, "Plugin")

        self.logger.info("Load success!")

    def loadPlugin(self, cls, typ):
        self.logger.info("Loading Kyouka "+typ)
        c = cls.pluginInfo['entrance']
        if cls.pluginInfo['packageName'] in self.config.get('DisablePlugin', []):
            self.logger.info("插件 %s(%s) 被配置禁止加载" % (
                cls.pluginInfo['name'], cls.pluginInfo['packageName']))
            return
        self.logger.info(typ + "find: "+cls.pluginInfo['name'])
        p: IPlugin = c(msgBusPort=self.msgBus.getPort(typ),
                       configRoot=self.configRoot, logSerivce=self.logSerivce, KyoukaAPI=self.KyoukaAPI)
        p.start()
        self.logger.info(typ + "loading: "+cls.pluginInfo['name'])
        if not p._IPlugin__loadReady.wait(15):
            self.logger.error("未在时限内完成初始化，退出")
            exit()
        if typ == "Bridge":  # 保存引用
            if p.msgBusPort.name in self.bridgeInfo.keys():
                self.logger.error("发现重复载入了名称相同的 Bridge，退出")
                exit()
            self.bridgeInfo[p.msgBusPort.name] = p
        p._IPlugin__startReceiveMsgThread()

    def asyncInit(self):
        """
        初始化协程线程
        """
        self._loop = asyncio.new_event_loop()  # 创建消息循环
        asyncio.set_event_loop(self._loop)
        self._t = threading.Thread(
            target=self._asyncLoopThread)  # 在新线程以协程方式转发消息
        self._t.name = "Kyouka Async Loop"
        self._t.start()

    def _asyncLoopThread(self):
        """
        协程事件循环
        """
        self.logger.info("Kyouka 协程消息循环启动")
        # asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
        self.logger.debug("Kyouka 协程消息循环启动")

    async def coreMonitor(self):
        self.logger.info("coreMonitor start")
        while True:
            msg = await self.msgBus._pluginSendBus.get()
            if self.msgBus._msgEventRoute(msg) == 'C':
                pass  # TODO
            else:
                self.logger.warn(
                    "coreMonitor: Not a Core Event type type, discard")
