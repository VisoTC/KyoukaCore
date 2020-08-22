import logging
from logging import log
from os import path
from Interface.IBridge import IBridge
import os
import importlib
from ..Interface import IPlugin
from ..Core.Logger import LogSerivce
from .Exception import PluginTypeNotSupport,PluginNotSupport

class PluginManager():
    logger = LogSerivce()

    Bridges = {}
    Plugeins = {}

    def __init__(self) -> None:
        logging.debug("PluginManager: Start load")
        self.loadPlugin(self.findPlugin("Bridge"),'Bridge')
        self.loadPlugin(self.findPlugin("Plugin"),'Plugin')
        logging.debug("PluginManager: Load success")


    def findPlugin(self,pType:str):
        if not (pType == "Bridge" or pType == "Plugin"):
            raise PluginTypeNotSupport
        searchPath = os.path.abspath(os.getcwd(), pType)
        logging.debug("PluginManager.findPlugin:Search Path: {path}".format(path=searchPath))
        pluginFile = []
        for pfile in os.listdir(searchPath):
            if pfile == "__pycache__":
                continue
            logging.debug("PluginManager.findPlugin:find {name}@{type}".format(name=pfile,type=pType))
            pluginFile.append(pfile)
        return pluginFile
    
    def loadPlugin(self,pType:str,pluginFile):
        if not (pType == "Bridge" or pType == "Plugin"):
            raise PluginTypeNotSupport
        for preLoadPluginName in pluginFile:
            preLoadPlugin = importlib.import_module("{pType}.{name}".format(pType=pType,name=preLoadPluginName))# 动态载入模块
            logging.debug("PluginManager.loadPlugin:load {pType}.{name}".format(pType=pType,name=preLoadPluginName))
            if not "pluginInfo" in dir(preLoadPlugin): # 确认是否有插件信息
                raise PluginNotSupport
            if not ('packageName' in preLoadPlugin.pluginInfo.keys() and 
                        'name' in preLoadPlugin.pluginInfo.keys() and
                        'version' in preLoadPlugin.pluginInfo.keys() and
                        'entrance' in preLoadPlugin.pluginInfo.keys() and
                        'author' in preLoadPlugin.pluginInfo.keys()):
                raise PluginNotSupport
            logging.debug("PluginManager.loadPlugin:plugin info:\npackageName:{packageName}\nname:{name}\nversion{version}\nauthor{author}".format(**preLoadPlugin.pluginInfo))
            # 确认是否为指定类派生的类
            LoadPlugin = preLoadPlugin.pluginInfo['entrance'] # 找到入口类
            if pType == 'Plugin' and not issubclass(LoadPlugin,IPlugin):# 判断入口类是否是预期
                self.logger.error("The plugin does not meet the requirements")
                raise PluginNotSupport
            if pType == 'Bridge' and not issubclass(LoadPlugin,IBridge):
                self.logger.error("The plugin does not meet the requirements")
                raise PluginNotSupport
            # 初始化类并添加到字典以便于管理
            loadPlugin = LoadPlugin()
            if pType == 'Plugin':
                if not loadPlugin.pluginInfo['packageName'] in self.Plugeins.keys(): # 包名冲突不载入
                    self.Plugeins[loadPlugin.pluginInfo['packageName']] = loadPlugin
                else:
                    logging.WARN("PluginManager.loadPlugin:package {pn}({n}@{t}) loading conflict, loading has been skipped".format(pn=loadPlugin.pluginInfo['packageName'],name=preLoadPluginName,t=pType))
                    continue
            elif pType == 'Bridge':
                if not loadPlugin.pluginInfo['packageName'] in self.Bridges.keys():
                    self.Bridges[loadPlugin.pluginInfo['packageName']] = loadPlugin
                else:
                    logging.WARN("PluginManager.loadPlugin:package {pn}({n}@{t}) loading conflict, loading has been skipped".format(pn=loadPlugin.pluginInfo['packageName'],name=preLoadPluginName,t=pType))
                    continue
            loadPlugin.name = loadPlugin.pluginInfo['packageName'] # 线程名为包名
            # 启动插件
            loadPlugin.start()# 启动线程
            logging.debug("PluginManager.loadPlugin:{pType}.{name} is loaded".format(pType=pType,name=preLoadPluginName))
