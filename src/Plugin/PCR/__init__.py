import json
import re
from Core.Interface.UserObj import Group
import time
from typing import Union, List
from Core.Interface.IPlugin import IPlugin

from Core.Interface.Msg.MsgBase import MsgEvent
from Core.Interface.Msg.MsgInfo import GroupMsgInfo, PrivateMsgInfo
from Core.Interface.Msg.MsgContent import AtMsg, MsgContent, TextMsg, PicMsg
from redis import StrictRedis as Redis
from .main import PCR


class PCRBOT(IPlugin):

    @staticmethod
    def PluginInfo():
        '''
        插件信息
        :return Config
        '''
        return {
            "packageName": "com.visotc.KyoukaCore.PCR",  # 包名，唯一标识
            "name": "PCR 报刀插件",  # 显示名称
            "version": "dev",  # 版本号
            "author": "Viso-TC",  # 作者
            "entrance": PCRBOT  # 入口类
        }

    @property
    def pluginInfo(self):
        return self.PluginInfo()

    def printMsg(self, msg):

        print("""\nBridge: {} \n{}:{}{}""".format(msg.bridge, msg.msgInfo, msg.msgContent,
                                                  ("\n@" + "@".join(msg.msgContent.atUser)) if not len(msg.msgContent.atUser) > 0 else ""))
        self.msgBusPort.send(MsgEvent(**{"bridge": msg.bridge,
                                         "time": int(time.time()),
                                         "msgInfo": GroupMsgInfo(msg.msgInfo.GroupId),
                                         "msgContent": [AtMsg(msg.msgInfo.UserId), TextMsg("复读："+msg.msgContent.content), ]
                                         }))

    def report(self, msg: MsgEvent):
        damage = msg.msgContent[0].content[2:]
        if not damage.isdigit():
            self._reply(msg, TextMsg(
                "PCR 报刀插件：需要输入整数哦", atUser=[msg.msgInfo.UserId]))
        else:
            resp = self.pcr.reportScore(
                msg.msgInfo.GroupId, msg.msgInfo.UserId, int(damage))
            infos = self.pcr.queryDamageASMember(
                msg.msgInfo.GroupId, msg.msgInfo.UserId)
            # 计算刀数
            k = 0
            bk = 0
            for info in infos:
                k += 1
                if info.kill == 1:
                    bk += 1
            kMsg = "今日已出{}刀（完整刀{}刀）".format(
                str(k), str(k-bk))
            if resp[1]:
                sendMsg = "已造成伤害：{}并击败\n{}\n{}"
            else:
                sendMsg = "已造成伤害：{}\n{}\n{}"
            self._reply(msg, TextMsg(
                sendMsg.format(format(int(damage), ','), kMsg, resp[0])), atReply=True)

    def OnFromGroupMsg(self, msg):
        if len(msg.msgContent) >= 1:
            if isinstance(msg.msgContent[0], TextMsg):
                msgText = msg.msgContent[0]
                if self.currentPeriod is None:
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件：尚未设置当前阶段，功能暂时不可用"), atReply=True)
                if msgText.content[0:2] == "报刀":
                    self.report(msg)
                elif msgText.content.lower() == "/pcr BOSS情况":
                    self._reply(msg, TextMsg(
                        self.pcr.currentBossInfo(msg.msgInfo.GroupId)), atReply=True)
                elif msgText.content.lower() == "/pcr 我的情况":
                    infos = self.pcr.queryDamageASMember(
                        msg.msgInfo.GroupId, msg.msgInfo.UserId)
                    sendMsg = ''
                    for info in infos:
                        sendMsg += str(info) + "\n"
                    self._reply(msg, TextMsg(
                        sendMsg if len(sendMsg) != 0 else "今日还没有击败信息哦"), atReply=True)
                elif msgText.content[0:4] == "/pcr":
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件：当前可用命令\n报刀[伤害值]：报刀\n/pcr BOSS情况：返回当前 BOSS 信息\n/pcr 我的情况：返回今日的出刀情况"), atReply=True)

    def OnFromPrivateMsg(self, msg):
        if len(msg.msgContent) >= 1:
            if isinstance(msg.msgContent[0], TextMsg):
                msgText = msg.msgContent[0]
                if msgText.content.find("/pcr login ") == 0:
                    self.apiLogin(msg)
                elif msgText.content[0:4] == "/pcr":
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件：当前可用命令\n/pcr login：登录到WebAPI"))

    def apiLogin(self, msg):
        code = msg.msgContent[0].content.replace("/pcr login ", "", 1)
        if self.redis.expire("KyoukaAPI@Code@%s" % code, 30) == 0:
            self._reply(msg, TextMsg("登录代码已过期，请刷新页面"))
            return
        myUid = msg.msgInfo.UserId
        token = self.redis.get("KyoukaAPI@Code@%s" % code)
        Groups = []
        for g in self.kyoukaAPI.groupList(msg.bridge):
            isAdmin = False
            if g.own.uid == myUid or g.member.get(myUid).isAdmin:
                isAdmin = True
            m = []
            for gm in g.member:
                m.append({
                    'uid': gm.uid,
                    'nickName': gm.nickName,
                    'isAdmin': gm.isAdmin
                })
            Groups.append({
                'gid': g.gid,
                'name': g.name,
                'isAdmin': isAdmin,
                'own': {
                    'nickName': g.own.nickName,
                    'uid': g.own.uid
                },
                'member': m
            })
        s = {
            'user': {
                'uid': myUid,
                'nickName': self.kyoukaAPI.friendsList(msg.bridge).get(myUid).nickName
            },
            'groups': Groups
        }
        js = json.dumps(s, ensure_ascii=False)
        self.redis.set("KyoukaAPI@%s" % token, js, ex=60*15)  # 初始化会话信息
        self._reply(msg, TextMsg("已授权登录"))

    def run(self):
        self.logger.info("载入 PCR 插件")
        self.redis = Redis(host='127.0.0.1', port=6379,
                           db=0, decode_responses=True)
        self.currentPeriod = "Leo"
        self.pcr = PCR({
            'database': "pcr",
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root',
            'passwd': '123'
        }, self.currentPeriod)
        self.callback(self.OnFromGroupMsg, GroupMsgInfo)
        self.callback(self.OnFromPrivateMsg, PrivateMsgInfo)
        self.loadDone()
        # self.main()


def no():
    import sqlite3
    from Class.DataBase import SqliteDataBase
    from plugin.PCR.main import PCR

    s = SqliteDataBase("t.db")  # :memory:
    s.origin.execute('''CREATE TABLE "damage" (
        "time" BIGINT NOT NULL,
        "period" TEXT NOT NULL,
        "stage" INTEGER NOT NULL,
        "step" INTEGER NOT NULL,
        "member" INTEGER NOT NULL,
        "damage" INTEGER NOT NULL,
        "kill" INTEGER NULL DEFAULT 0
    )''')
    pcr = PCR(s)
    print(pcr.reportScore("0", 3000000))
    print(pcr.reportScore("0", 3000000))
    print()
    print(pcr.currentBossInfo())
    print()
    print(pcr.reportScore("0", 6000000))
    b = pcr.queryDamageASMember("0", "20200805")
    print("击杀报告")
    for row in b:
        print(row)


pluginInfo = PCRBOT.PluginInfo()
