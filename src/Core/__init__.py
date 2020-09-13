import logging
from .Config import Config
from .LoadService import LoadService
from .Service import ServiceManager

__DisableService__ = []


class LogLevel():
    logDic = {
        'CRITICAL': logging.CRITICAL,
        'FATAL': logging.FATAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'WARN': logging.WARN,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'NOTSET': logging.NOTSET,
    }

    @classmethod
    def toLevel(cls, s: str):
        return cls.logDic.get(s.upper(), logging.INFO)


class KyoukaCore():
    def __init__(self) -> None:
        self.logger = logging.getLogger("KyoukaCore")
        self.logger.setLevel(logging.INFO)
        self._config = Config("KyoukaCore")
        if self._config.isEmpty:
            self.logger.info("初始化配置文件")
            self._config.data = {
                "ConfigVersion": "1",
                "LogLevel": "info",
                "disableService": [],
            }
            self._config.commit()
        else:
            logging.basicConfig(
                level=LogLevel.toLevel(self._config['LogLevel']))
            self.logger.info("载入配置文件")
            __DisableService__ = self._config['disableService']
        self.logger.info("载入 Service")
        self._serviceManager = ServiceManager()
        self._loadService = LoadService()
        self._loadService.load()
        self.logger.info("完成")
        self._serviceManager.wait()
