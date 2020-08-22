import logging


class LogSerivce():
    """
    日志服务

    单例
    """
    __Instance = None
    __isGetCoreLogger = False

    def __new__(cls, *args, **kwargs):
        if cls.__Instance is None:
            cls.__Instance = object.__new__(cls)
        return cls.__Instance

    def __init__(self): ...

    @staticmethod
    def configLogger(logger: logging.Logger):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter)
        logger.logHandler = logging.StreamHandler()
        logger.setLevel(logging.INFO)

    def getCoreLogger(self):
        if self.__isGetCoreLogger:
            raise Exception
        self.Corelogger = self.getLogger("KyoukaCore")
        self.configLogger(self.Corelogger)
        self.Corelogger.info("日志服务启动")
        self.__isGetCoreLogger = True
        return self.Corelogger

    def getLogger(self, name):
        logger = logging.getLogger(name)
        logger.logHandler = logging.StreamHandler()
        logger.setLevel(logging.DEBUG)
        self.configLogger(logger)
        return logger
