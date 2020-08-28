import json
from os.path import join
import random
import base64
import os
from Core.Interface.IPlugin import IPlugin
from Core.Interface.Msg.MsgBase import MsgEvent
from Core.Interface.Msg.MsgContent import TextMsg, PicMsg
from time import sleep, time
import requests

from Core.Interface.Msg.MsgInfo import GroupMsgInfo


class Setu(IPlugin):

    @staticmethod
    def PluginInfo():
        '''
        插件信息
        :return Config
        '''
        return {
            "packageName": "com.visotc.KyoukaCore.setu",  # 包名，唯一标识
            "name": "瑟图",  # 显示名称
            "version": "v1.dev",  # 版本号
            "author": "Viso-TC",  # 作者
            "entrance": Setu  # 入口类
        }
    last_time = 0

    @property
    def pluginInfo(self):
        return self.PluginInfo()

    def hso(self, msg):
        if random.randint(0, 9) < 4 or self.last_time * 30 >= time():
            with open(os.path.join(os.path.split(os.path.realpath(__file__))[0], 'テンパランス.png'), 'rb') as テンパランス:
                pic = PicMsg(テンパランス)
            self._reply(msg, [pic, TextMsg("\n节制 (能力技) 为自身附加状态：节制  持续时间：20秒\n" +
                                           "节制效果：自身发动治疗魔法的治疗量提高20%，每3秒为自身及30米内队员附加状态：节制，受到的伤害减轻10%。\n" +
                                           "持续时间：5秒 \n习得条件　　白魔法师80级\n适应职业　　白魔法师\n复唱时间　　120秒")])
            return
        self.logger.info("开始发送瑟图")
        self._reply(msg, TextMsg("收到！"))
        r = requests.get('https://api.lolicon.app/setu/', params={
            'apikey': self.apikey,
            'size1200': 1,  # 获得小尺寸版本
            'keyword': 'プリンセスコネクト!Re:Dive'
        })
        resp = r.json()
        if resp['code'] != 0:
            if resp['code'] == -1:
                self._reply(msg, TextMsg("瑟图 API 发生内部错误"))
            else:
                self._reply(msg, TextMsg("瑟图 API 错误：%s" % resp['msg']))
        self.last_time = time()
        if(resp['count'] == 0):
            self._reply(msg, TextMsg("找不到瑟图了"))
        pic = PicMsg.webImg(resp['data'][0]['url'])
        text = "《{}》（pid:{})作者：   {}".format(
            resp['data'][0]['title'], resp['data'][0]['pid'], resp['data'][0]['author'])
        self._reply(msg, pic)
        self._reply(msg, TextMsg(text))

    def fromGroupMsgInfo(self, msg):
        # 只接受文本消息
        if len(msg.msgContent) != 1 and not isinstance(msg.msgContent[0], TextMsg):
            return
        else:
            if isinstance(msg.msgContent[0], TextMsg):
                testMsg = msg.msgContent[0]
            else:
                return
        if testMsg.content == "来张瑟图" or testMsg.content == "/hso":
            self.hso(msg)

    def run(self):
        helpText = "请在此输入 APIKey"
        self.apikey = self.config.get('apikey', helpText)
        if self.apikey == helpText:
            self.config['apikey'] = helpText
            self.config.commit()
            self.logger.error("需要瑟图 APIKEY，请在配置文件中输入后重新启动，插件将不会载入")
            sleep(3)
        else:
            self.callback(self.fromGroupMsgInfo, GroupMsgInfo)
        self.loadDone()


pluginInfo = Setu.PluginInfo()
