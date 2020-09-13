# 统一的配置管理类
import collections
import logging
import os
import sys
import json
import copy
import threading


class ConfigFactory():
    _instance_lock = threading.Lock()
    __isInit = False

    def __new__(cls, *args, **kwargs):
        if not hasattr(ConfigFactory, "_instance"):
            with ConfigFactory._instance_lock:
                if not hasattr(ConfigFactory, "_instance"):
                    ConfigFactory._instance = super(
                        ConfigFactory, cls).__new__(cls)
        return ConfigFactory._instance

    def __init__(self) -> None:
        if not self.__isInit:
            self.logger = logging.getLogger("KyoukaCore Config")
            self.filePath = os.path.join(
                sys.path[0], "config.json")
            if os.path.exists(self.filePath):
                with open(self.filePath) as configFile:
                    tmpConfig: dict = json.loads(configFile.read())
                    self.__config = tmpConfig
            else:
                self.__config = {}
            self.__isInit = True


    def getConfig(self, packageName):
        if not packageName in self.__config.keys():
            return dict()
        else:
            return copy.deepcopy(self.__config[packageName])

    def save(self):
        self.logger.info("Save config...")
        with open(self.filePath, 'w') as cfile:
            cfile.write(json.dumps(self.__config,
                                   indent=4, ensure_ascii=False))

    def commit(self, config):
        self.__config[config.packageName] = copy.deepcopy(config.data)
        self.save()


class Config(collections.UserDict):
    def __init__(self, packageName: str) -> None:
        """
        配置文件
        :param packageName: 包名
        """
        self.__packageName = packageName
        self.__configRoot = ConfigFactory()
        self.data = self.__configRoot.getConfig(self.__packageName)

    @property
    def packageName(self):
        return self.__packageName

    @property
    def isEmpty(self):
        return len(self.data.keys()) == 0

    def commit(self):
        """
        提交更改到配置，必须执行此方法才能同步修改到系统配置核心
        """
        self.__configRoot.commit(self)
