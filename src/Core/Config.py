# 统一的配置管理类
import collections
from logging import Logger
import os,sys
import json
import copy


class ConfigFactory():
    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.filePath = os.path.join(
            sys.path[0], "config.json")
        if os.path.exists(self.filePath):
            with open(self.filePath) as configFile:
                tmpConfig: dict = json.loads(configFile.read())
                if not "KyoukaBot" in tmpConfig.keys():
                    tmpConfig = self.initConfig()
                if tmpConfig["KyoukaBot"]['configVersion'] != "1":
                    # 可在此进行配置版本升级操作，若版本无法处理直接初始化
                    tmpConfig = self.initConfig()
                    self.save()
                self.__config = tmpConfig
        else:
            self.__config = self.initConfig()
            self.save()

    def initConfig(self):
        self.logger.info("Init config...")
        return {
            "KyoukaBot": {
                "configVersion": "1",
                "LogLevel": "info",
                "adminUser": ""
            }
        }

    def getConfig(self, packageName):
        if not packageName in self.__config.keys():
            return dict()
        else:
            return copy.deepcopy(self.__config[packageName])

    def save(self):
        self.logger.info("Save config...")
        with open(self.filePath, 'w') as cfile:
            cfile.write(json.dumps(self.__config, indent=4))

    def commit(self, config):
        self.__config[config.packageName] = copy.deepcopy(config.data)
        self.save()


class Config(collections.UserDict):
    def __init__(self, configRoot: ConfigFactory, packageName: str) -> None:
        """
        初始化配置，专用于某个插件，隔离
        :param configRoot: Config 根对象
        :param packageName: 包名
        """
        self.__packageName = packageName
        self.__configRoot = configRoot
        self.data = self.__configRoot.getConfig(self.__packageName)

    @property
    def packageName(self):
        return self.__packageName

    def commit(self):
        """
        提交更改到配置，必须执行此方法才能同步修改到系统配置核心
        """
        self.__configRoot.commit(self)
