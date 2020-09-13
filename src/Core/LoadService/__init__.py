import importlib
import sys
import os
import logging
from typing import Optional

from .exception import NotDirException

from ..Service import ServiceType
from ..Service.exception import ServiceRegisterFailerException
from ..Config import Config


class LoadService():
    def __init__(self, loadPath: Optional[str] = None) -> None:
        self.logger = logging.getLogger("KyoukaCore")
        if loadPath is None:
            self._loadPath = sys.path[0]
        else:
            self._loadPath = loadPath

    def _loadService(self, T: ServiceType):
        if T == ServiceType.Plugin:
            loadDir = "Plugin"
        elif T == ServiceType.Bridge:
            loadDir = "Bridge"
        else:
            raise ValueError
        self.logger.info("开始载入 {}".format(loadDir))
        if not os.path.isdir(os.path.join(self._loadPath, loadDir)):
            self.logger.error("找不到文件夹 {}".format(loadDir))
            return
        for path in os.listdir(os.path.join(self._loadPath, loadDir)):
            if path[0] == "_":
                continue
            paths = path.split('.')
            if len(paths) == 1:
                if os.path.isdir(os.path.join(self._loadPath, loadDir, paths[0])):
                    if os.path.exists(os.path.join(self._loadPath, loadDir, paths[0], "__init__.py")):
                        self._load("{}.{}".format(loadDir, paths[0]))
                    else:
                        self.logger.warn("忽略文件夹：{}".format(
                            os.path.join(self._loadPath, loadDir, path)))
                    continue
            elif len(paths) == 2:
                if paths[1].lower() == "py":
                    self._load("{}.{}".format(loadDir, paths[0]))
                    continue
            self.logger.warn("忽略文件：{}".format(
                os.path.join(self._loadPath, loadDir, path)))

    def _load(self, name: str):
        try:
            importlib.import_module(name)
        except IndentationError as e:
            self.logger.error("文件(%s)中有文件错误：行 %s:%s"%(e.filename,e.lineno,e.offset))
            

    def load(self):
        self._loadService(ServiceType.Bridge)
        self._loadService(ServiceType.Plugin)
