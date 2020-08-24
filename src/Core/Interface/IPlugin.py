from Core.Interface.Msg.MsgContent import MsgContent, TextMsg, AtMsg
from Core.Interface.Msg.MsgBase import MsgEvent
from Core.Interface.Msg.MsgInfo import MsgInfo, GroupMsgInfo, PrivateMsgInfo

from typing import Dict, List, Union
from Core.MsgBus import MsgBusPort
from abc import ABCMeta, abstractmethod

import threading
import time

from Core.Config import Config, ConfigFactory
from Core.Logger import LogSerivce


class Ready(threading.Event):
    def wait(self, timeout=15):
        return super().wait(timeout=timeout)


class IPlugin(threading.Thread, metaclass=ABCMeta):
    def __init__(self, msgBusPort: MsgBusPort, configRoot: ConfigFactory, logSerivce: LogSerivce, KyoukaAPI) -> None:
        threading.Thread.__init__(
            self, daemon=True, name=self.pluginInfo['packageName'])
        self._IPlugin__MsgBusPort = msgBusPort  # 消息总线
        self._IPlugin__LogSerivce = logSerivce  # 日志服务

        self._IPlugin__setlogger()

        self._IPlugin__config = Config(
            configRoot, self.pluginInfo['packageName'])  # 配置服务

        self._IPlugin__KyoukaAPI = KyoukaAPI  # API 服务

        self._IPlugin__callback: Dict[str, List] = {}  # 回调字典

        self._IPlugin__commandRoot: str = None  # 命令路由根目录
        self._IPlugin__command: Dict[str, List] = {}  # 回调字典

        self._IBridge__init()  # 初始化桥的内容

        self._IPlugin__loadReady = Ready()  # 加载完成指示器

    def _IBridge__init(self): ...  # 仅在桥类可用

    def loadDone(self):
        self.msgBusPort.name = "Plugin"
        self._IPlugin__loadReady.set()

    @abstractmethod
    def run(self):
        """
        插件主线程，若有需要可以阻塞此线程\n
        调用逻辑：\n
        [Bridge] 就绪后调用 self.loadDone(<name>)设定当前 Bridge 的身份，便于插件指定发送的 Bridge\n
        [Plugin] 直接调用 self.loadDone()\n
        Core 将会阻塞加载进程直到调用 self.loadDone() 后启动消息循环
        """

    @property
    def kyoukaAPI(self):
        """
        API 接口
        """
        return self._IPlugin__KyoukaAPI

    @property
    def logger(self):
        """
        Log 接口
        """
        return self._IPlugin__logger

    @property
    def msgBusPort(self) -> MsgBusPort:
        '''
        事件总线端口
        :return MsgBusPort
        '''
        return self._IPlugin__MsgBusPort

    @property
    def config(self):
        '''
        暴漏在内部的简易配置文件，底层将以 JSON 储存在统一的配置文件中
        修改后请调用 commit() 方法同步更改到 Root Config 对象
        :return Config
        '''
        return self._IPlugin__config

    @staticmethod
    @abstractmethod
    def pluginInfo():
        '''
        插件信息
        :return Config
        '''
        return {
            "packageName": "com.visotc.KyoukaCore.IPlugin",  # 包名，唯一标识
            "name": "IPlugin",  # 显示名称
            "version": "1",  # 版本号
            "author": "Viso-TC",  # 作者
        }

    def callback(self, func, msgInfo: MsgInfo):
        """
        注册一个消息回调
        :param msgType: 注册的消息类别
        """
        try:
            msgType = self._IPlugin__MsgInfo2StrHelper(msgInfo)
        except TypeError:
            self.logger.warn("类（%s）无法注册到消息回调", msgInfo)
            return False
        if not msgType in self._IPlugin__callback.keys():
            self.logger.debug("已注册消息回调："+msgType)
            self._IPlugin__callback[msgType] = []
            self._IPlugin__callback[msgType].append(func)
        else:
            if not func in self._IPlugin__callback[msgType]:
                self.logger.debug("已注册消息回调："+msgType)
                self._IPlugin__callback[msgType] = [func]
            else:
                self.logger.warn("消息回调: "+msgType+" 已经注册")
                return False
        return True

    def initCommandRouter(self, rootName):
        """
        TODO: 还没写完
        初始化命令路由
        :param rootName: 根命令（不需要带/）
        """
        self._IPlugin__commandRoot = rootName
        self.callback(self._IPlugin__CommandRouter, GroupMsgInfo(1, 1, 1, 1))

    def registerCommand(self, func, command: List[str], doc: str, kwargs: List[str] = list()):
        """
        TODO: 还没写完
        注册一条命令
        :param func: 回调命令
        :param command: 命令路径
        :param doc: 文档，用于解释命令的作用，用于 help 方法提供解析
        :param kwargs: 执行命令需要的命名参数
        """
        pointer = self._IPlugin__command
        if self._IPlugin__commandRoot is None:
            self.logger.error("需要先设置插件的根命令")
            return
        if len(command) <= 0:
            return
        for c in command:
            if not c in pointer.keys():
                pointer[c] = {
                    "func": None,
                    'kwargs': kwargs,
                    'doc': doc,
                    "sub": {}
                }
            pointer = pointer[c]["sub"]
        else:
            pointer["func"] = func

    def _reply(self, msg: MsgEvent, Contents: Union[List[MsgContent], MsgContent], atReply: bool = False):
        """
        快速回复帮助方法
        :param msg: 被回复的消息事件
        :param Content: 回复的消息串
        :param atReply: 是否 @ 被回复者
        """
        if not isinstance(Contents, list):
            Contents = [Contents]
        if atReply:
            Contents = [AtMsg(msg.msgInfo.UserId)] + Contents

        self.msgBusPort.send(MsgEvent(**{"bridge": msg.bridge,
                                         "time": int(time.time()),
                                         "msgInfo": msg.msgInfo,
                                         "msgContent": Contents
                                         }))

    def _IPlugin__CommandRouter(self, msg):
        """
        TODO: 还没写完
        命令路由
        """
        if isinstance(msg.msgInfo, GroupMsgInfo):
            if isinstance(msg.msgContent, TextMsg):
                commands = self._IPlugin__CommandSplitHelper(
                    msg.msgContent.content)
                pointer = self._IPlugin__command
                endindex = enumerate(commands) - 1
                for i, command in enumerate(commands):
                    if i == 0:
                        if not command == "/" + self._IPlugin__commandRoot:  # 匹配不到根目录直接退出
                            break
                    else:
                        if i == endindex:  # 到达命令最后一位
                            if pointer['func'] is None:  # 没有匹配到命令
                                self._reply(msg, TextMsg(
                                    "无法匹配到可执行命令\n" + self._IPlugin__HelpCommand(pointer, commands)))  # 调用帮助信息
                        if len(pointer['sub']) == 0:  # 没有子命令了
                            pass

    def _IPlugin__HelpCommand(self, pointer, ic, commands):
        contant = "/"
        for i, c in enumerate(commands):
            if i > ic:
                break
            contant += (c + " ")
        for arg in pointer['kwargs']:
            contant += "<%s> " % arg
        contant += ": "
        if pointer['doc'] is None or pointer['doc'] == "":
            contant += pointer['doc']
        else:
            contant += "无帮助信息"
        return contant

    def _IPlugin__CommandSplitHelper(self, text):
        keep = None
        commandSplit = []
        tmp = ""
        for t in text:
            if not keep in None and t == keep:
                keep = None
            if t == " ":  # 遇到分隔符算入命令中
                commandSplit.append(tmp)
                tmp = ""
                continue
            tmp += t
        return commandSplit

    def _IPlugin__MsgInfo2StrHelper(self, msgInfo: MsgInfo):
        """
        MsgInfo 类 => 文本帮助方法
        :param msgInfo: MsgInfo 类的子类
        :return: 转换后的文本
        :raise TypeError: 未定义的类转文本或非 MsgInfo 类及其子类
        """
        try:  # 如果是实例就让调用实例帮助类
            issubclass(msgInfo, MsgInfo)
        except TypeError:
            return self._IPlugin__MsgInfoObj2StrHelper(msgInfo)
        if not issubclass(msgInfo, MsgInfo):
            raise TypeError
        elif issubclass(msgInfo, GroupMsgInfo):
            return "GroupMsg"
        elif issubclass(msgInfo, PrivateMsgInfo):
            return "PrivateMsg"
        else:
            raise TypeError

    def _IPlugin__MsgInfoObj2StrHelper(self, msgInfo: MsgInfo):
        """
        MsgInfo 实例 => 文本帮助方法
        :param msgInfo: MsgInfo 类的子类
        :return: 转换后的文本
        :raise TypeError: 未定义的类转文本或非 MsgInfo 类及其子类
        """
        if not isinstance(msgInfo, MsgInfo):
            raise TypeError
        elif isinstance(msgInfo, GroupMsgInfo):
            return "GroupMsg"
        elif isinstance(msgInfo, PrivateMsgInfo):
            return "PrivateMsg"
        else:
            raise TypeError

    def _IPlugin__startReceiveMsgThread(self):
        """
        请勿自行调用
        Core 调用时机，当插件报告已经就绪时
        """
        self._IPlugin__rmt = threading.Thread(target=self._IPlugin__receiveMsgThread,
                                              name=self.pluginInfo['packageName']+".ReceiveMsgThread")
        self._IPlugin__rmt.start()
        self.logger.info("消息监听线程启动")

    def _IPlugin__receiveMsgThread(self):
        """
        消息循环
        """
        while True:
            msg = self.msgBusPort.receive()
            if not isinstance(msg, MsgEvent):
                self.logger.warn('丢弃无法识别的事件')
                continue
            else:
                try:
                    if len(self._IPlugin__callback.get(self._IPlugin__MsgInfo2StrHelper(msg.msgInfo), {})) == 0:
                        self.logger.warn(
                            "消息类型：%s 没有匹配到 Callback 方法，丢弃", self._IPlugin__MsgInfo2StrHelper(msg.msgInfo))
                        continue
                    for func in self._IPlugin__callback.get(self._IPlugin__MsgInfo2StrHelper(msg.msgInfo), {}):
                        func(msg)
                except Exception as e:
                    self.logger.exception(e)
                    self._reply(msg, TextMsg(
                        "KyoukaCore: [%s]在处理消息内容时发生错误" % self.pluginInfo['name']),atReply=True)
                    continue

    def _IPlugin__setlogger(self):
        """
        设定 Logger 的名称
        """
        self._IPlugin__logger = self._IPlugin__LogSerivce.getLogger(
            "{name}@plugin".format(name=self.pluginInfo['name']))
