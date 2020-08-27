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

from Plugin.PCR.orm import damage
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

    def report(self, gid, uid, damage, stage=None, step=None):
        if not damage.isdigit():
            return "PCR 报刀插件：需要输入整数哦"
        else:
            if not (stage == None or step == None):
                if not (stage == None and step == None):
                    if not stage >= 1:
                        return "PCR 报刀插件：周目需要大于1哦"
                    if not (step >= 1 or step < 6):
                        return "PCR 报刀插件：BOSS 位置需要在 1-5 之间哦"
                else:
                    return "请同时输入周目与 BOSS 位置"
            resp = self.pcr.reportScore(
                gid, uid, int(damage), stage, step)
            queryDamage = self.pcr.queryDamageASMember(gid, uid)
            allK, fullK = queryDamage.getK()
            kMsg = "[{}]今日已出{}刀（完整刀{}刀）".format(queryDamage[-1].KType,
                                                str(allK), str(fullK))
            if resp[1]:
                sendMsg = "已造成伤害：{}并击败\n{}\n{}"
            else:
                sendMsg = "已造成伤害：{}\n{}\n{}"
            return sendMsg.format(format(int(damage), ','), kMsg, resp[0]), resp[0]

    def OnFromGroupMsg(self, msg):
        textMsg = None
        atMsg = None
        for m in msg.msgContent:
            if isinstance(m, TextMsg):
                if textMsg is None:
                    textMsg = m
                else:
                    self.logger.warn("重复消息链，抛弃")
            if isinstance(m, AtMsg):
                if atMsg is None:
                    atMsg = m
                else:
                    self.logger.warn("重复消息链，抛弃")
        if not textMsg is None:
            if self.currentPeriod is None:
                self._reply(msg, TextMsg(
                    "PCR 报刀插件：尚未设置当前阶段，功能暂时不可用"), atReply=True)
            if textMsg.content[0:2] == "报刀":
                report = self.report(msg.msgInfo.GroupId,
                                     msg.msgInfo.UserId,
                                     msg.msgContent[0].content[2:])
                if isinstance(report, tuple):
                    sendMsg = report[0]
                    cInfo = report[1]
                else:
                    sendMsg = report
                    cInfo = False
                self._reply(msg, TextMsg(sendMsg), atReply=True)
                if cInfo:
                    self.checkReserve(msg, cInfo)

            elif textMsg.content[0:7].lower() == "/pcr 报刀":
                if textMsg.content[7] != " ":
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件：指令之间需要插入空格哦"), atReply=True)
                    return
                splitStr = textMsg.content[8:].split(" ")
                damage = None
                stage = None
                step = None
                if len(splitStr) == 1:
                    damage = splitStr[0]
                elif len(splitStr) == 3:
                    damage = splitStr[0]
                    stage = int(splitStr[1])
                    step = int(splitStr[2])
                else:
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件：参数错误，需要三个参数，而你却输入了 %s 个" % str(len(splitStr))), atReply=True)
                    return
                report = self.report(msg.msgInfo.GroupId,
                                msg.msgInfo.UserId,
                                damage,
                                stage=stage,
                                step=step)
                if isinstance(report, tuple):
                    sendMsg = report[0]
                    cInfo = report[1]
                else:
                    sendMsg = report
                    cInfo = False
                self._reply(msg, TextMsg(sendMsg), atReply=True)
                if cInfo:
                    self.checkReserve(msg, cInfo)

            elif textMsg.content[0:7].lower() == "/pcr 代刀":
                try:
                    if textMsg.content[7] != " " and textMsg.content[7] != "@":
                        self._reply(msg, TextMsg(
                            "PCR 报刀插件：指令之间需要插入空格哦"), atReply=True)
                        return
                except IndexError:
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件：需要输入参数哦"), atReply=True)
                    return
                if atMsg is None:
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件，你需要@一个人才可以使用哦"), atReply=True)
                elif len(atMsg.atUser) != 1:
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件，需要@一个人,而你@了%s个" % len(atMsg)), atReply=True)
                else:
                    splitStr = textMsg.content.split("@")
                    if splitStr[0][0] != "/":
                        self._reply(msg, TextMsg(
                            "PCR 报刀插件：需要最先输入 /pcr 而不能直接@人再输入命令哦" % str(len(splitStr))), atReply=True)
                        return
                    splitStr = splitStr[0][8:].split(" ")
                    damage = None
                    stage = None
                    step = None
                    if len(splitStr) == 1:
                        damage = splitStr[0]
                    elif len(splitStr) == 3:
                        damage = splitStr[0]
                        stage = int(splitStr[1])
                        step = int(splitStr[2])
                    else:
                        self._reply(msg, TextMsg(
                            "PCR 报刀插件：参数错误，需要三个参数，而你却输入了 %s 个" % str(len(splitStr))), atReply=True)
                        return
                    if not (damage.isdigit() or stage.isdigit() or step.isdigit()):
                        self._reply(msg, TextMsg(
                            "PCR 报刀插件：参数错误，需要输入数字"), atReply=True)
                        return
                    report = self.report(msg.msgInfo.GroupId,
                                atMsg.atUser[0],
                                damage,
                                stage=stage,
                                step=step)
                    if isinstance(report, tuple):
                        sendMsg = report[0]
                        cInfo = report[1]
                    else:
                        sendMsg = report
                        cInfo = False
                    self._reply(msg, [TextMsg(sendMsg),
                        AtMsg([atMsg.atUser[0]])])
                    if cInfo:
                        self.checkReserve(msg, cInfo)

            elif textMsg.content.lower() == "/pcr boss情况" or textMsg.content.lower() == "/pcr boss":
                self._reply(msg, TextMsg(str(
                    self.pcr.currentBossInfo(msg.msgInfo.GroupId))), atReply=True)

            elif textMsg.content[:7].lower() == "/pcr 查刀":
                if not atMsg is None and len(atMsg.atUser) > 0:
                    if self.kyoukaAPI.groupList(msg.bridge).get(msg.msgInfo.GroupId).member.get(msg.msgInfo.UserId).isAdmin:
                        if len(atMsg.atUser) == 1:
                            uid = atMsg.atUser[0]
                        else:
                            self._reply(msg, TextMsg(
                                "PCR 报刀插件：需要@一个人,而你@了%s个" % len(atMsg)), atReply=True)
                            return
                    else:
                        self._reply(msg, TextMsg(
                            "PCR 报刀插件: 你必须是群管理员才有权限删除其他人的记录哦"), atReply=True)
                        return
                else:
                    uid = msg.msgInfo.UserId
                infos = self.pcr.queryDamageASMember(
                    msg.msgInfo.GroupId, uid)
                smsg = []
                if len(infos) != 0:
                    allK, fullK = infos.getK()
                    smsg.append("今日已出{all}刀（完整{full}刀）还剩下{left}刀".format(
                        all=allK, full=fullK, left=3-fullK))
                    for info in infos:
                        smsg.append("[{kname}]{time} {stage}周目{step}王{damage}".format(kname=info.KType,
                                                                                      time=info.timeStr,
                                                                                      stage=info.stage,
                                                                                      step=info.step,
                                                                                      damage=format(
                                                                                          info.damage, ',')))
                else:
                    smsg.append("PCR 报刀插件: 今日还未出刀哦")
                sendMsg = "\n".join(smsg)
                self._reply(msg, [TextMsg(sendMsg), AtMsg(uid)])

            elif textMsg.content[0:7].lower() == "/pcr 删刀":
                isAdmin = False
                if not atMsg is None and len(atMsg.atUser) > 0:
                    if self.kyoukaAPI.groupList(msg.bridge).get(msg.msgInfo.GroupId).member.get(msg.msgInfo.UserId).isAdmin:
                        if len(atMsg.atUser) == 1:
                            uid = atMsg.atUser[0]
                            isAdmin = self.kyoukaAPI.groupList(msg.bridge).get(
                                msg.msgInfo.GroupId).member.get(msg.msgInfo.UserId).isAdmin
                        else:
                            self._reply(msg, TextMsg(
                                "PCR 报刀插件，需要@一个人,而你@了%s个" % len(atMsg)), atReply=True)
                            return
                    else:
                        self._reply(msg, TextMsg(
                            "PCR 报刀插件: 你必须是群管理员才有权限删除其他人的记录哦"), atReply=True)
                        return
                else:
                    uid = msg.msgInfo.UserId
                d = self.pcr.delLastScore(
                    msg.msgInfo.GroupId, uid, isAdmin)
                if d is None:
                    self._reply(msg, TextMsg("找不到五分钟之内的报刀记录哦"), atReply=True)
                else:
                    self._reply(msg, TextMsg("记录：”{}“已被删除".format(str(d))
                                             ), atReply=True)

            elif textMsg.content.lower() == "/pcr 剩刀":
                self.urgeReport(msg)

            elif textMsg.content.lower() == "/pcr 催刀":
                if not self.memberIsAdmin(msg.bridge, msg.msgInfo.GroupId, msg.msgInfo.UserId):
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件: 你必须是群管理员才有权限使用此命令哦\,若要查询剩下刀数请使用'/pcr 剩刀'"), atReply=True)
                else:
                    self.urgeReport(msg, True)

            elif textMsg.content[:7].lower() == "/pcr 预约":
                try:
                    if textMsg.content[7] != " ":
                        self._reply(msg, TextMsg(
                            "PCR 报刀插件：指令之间需要插入空格哦"), atReply=True)
                        return
                except IndexError:
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件：需要输入参数哦"), atReply=True)
                    return
                step = textMsg.content[8:]
                if not step.isdigit():
                    self._reply(msg, TextMsg("需要输入数字，例如2，五王狂暴为6"))
                    return
                step = int(step)
                self._reply(msg, self.reserve(
                    msg.msgInfo.GroupId, msg.msgInfo.UserId, step))

            elif textMsg.content[:8].lower() == "/pcr 查预约":
                uid = msg.msgInfo.UserId
                if not atMsg is None and len(atMsg.atUser) > 0:
                    if self.kyoukaAPI.groupList(msg.bridge).get(msg.msgInfo.GroupId).member.get(msg.msgInfo.UserId).isAdmin:
                        if len(atMsg.atUser) == 1:
                            uid = atMsg.atUser[0]
                            isAdmin = self.kyoukaAPI.groupList(msg.bridge).get(
                                msg.msgInfo.GroupId).member.get(msg.msgInfo.UserId).isAdmin
                        else:
                            self._reply(msg, TextMsg(
                                "PCR 报刀插件，需要@一个人,而你@了%s个" % len(atMsg)), atReply=True)
                            return
                    else:
                        self._reply(msg, TextMsg(
                            "PCR 报刀插件: 你必须是群管理员才有权限查询其他人的预约哦"), atReply=True)
                        return
                self._reply(msg, self.reserveMemberList(
                    msg.msgInfo.GroupId, uid))

            elif textMsg.content[:7].lower() == "/pcr 鸽子":
                if textMsg.content[7] != " ":
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件：指令之间需要插入空格哦"), atReply=True)
                    return
                args = textMsg.content[8:].split(" ")
                if len(args) != 2:
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件：命令需要2个参数，而你却输入了{}个".format(len(args))), atReply=True)
                    return
                self._reply(msg, self.delReserve(msg.msgInfo.GroupId,
                                                 msg.msgInfo.UserId, args[0], args[1]), atReply=True)

            elif textMsg.content[0:4] == "/pcr":
                self._reply(msg, TextMsg(
                    "PCR 报刀插件：当前可用命令\n" +
                    "报刀[伤害值]：报刀\n" +
                    "/pcr 报刀 [伤害值] <周目> <位置>：报刀拓展版\n" +
                    "/pcr 代刀 [伤害值] <周目> <位置><@人>：代报刀\n" +
                    "/pcr 删刀：删除五分钟之内的刀\n" +
                    "/pcr BOSS：返回当前 BOSS 信息\n" +
                    "/pcr 查刀：返回今日的出刀情况\n" +
                    "/pcr 剩刀：报告未出完3刀的群员并告知剩余刀数\n"))
                self._reply(msg, TextMsg(
                    "/pcr 预约 [王]：当到达指定王发送@提醒\n" +
                    "/pcr 查预约：查询自己的预约记录\n" +
                    "/pcr 鸽子 [周目] [王]：取消预约记录\n"))
                self._reply(msg, TextMsg(
                    "仅限管理员：\n" +
                    "/pcr 删刀<@人>：删除被@的人的最后一刀\n" +
                    "/pcr 查刀<@人>：查询被@的人今日的出刀情况\n" +
                    "/pcr 催刀：自动@未出完3刀的群员并告知剩余刀数\n" +
                    "/pcr 查预约<@人>：查询被@的人的预约记录\n" +
                    "注意：若以/开头的命令所有参数必须用半角空格风格，\n" +
                    "　　　所有需要@人的不需要在命令和@之间插入空格"))

    def memberIsAdmin(self, bridge, gid, uid):
        try:
            return self.kyoukaAPI.groupList(bridge).get(gid).member.get(uid).isAdmin
        except:
            return False

    def OnFromPrivateMsg(self, msg):
        if len(msg.msgContent) >= 1:
            if isinstance(msg.msgContent[0], TextMsg):
                msgText = msg.msgContent[0]
                if msgText.content.find("/pcr login ") == 0:
                    self.apiLogin(msg)
                elif msgText.content[0:4] == "/pcr":
                    self._reply(msg, TextMsg(
                        "PCR 报刀插件：当前可用命令\n/pcr login：登录到WebAPI"))

    def urgeReport(self, msg: MsgEvent, at=False):
        left = {
            3: [],
            2: [],
            1: []
        }
        allLeftK = 0
        skipUid = [int(msg.bridge), 634108868]
        for m in self.kyoukaAPI.groupList(msg.bridge).get(msg.msgInfo.GroupId).member:
            if int(m.uid) in skipUid:  # 跳过指定用户
                continue
            queryDamage = self.pcr.queryDamageASMember(
                msg.msgInfo.GroupId, m.uid)
            _, fullK = queryDamage.getK()
            if fullK < 3:  # 完整刀不足三刀
                if 3-fullK == 3:
                    allLeftK += 3
                    left[3].append([m.uid, m.nickName])
                elif 3-fullK == 2:
                    allLeftK += 2
                    left[2].append([m.uid, m.nickName])
                elif 3-fullK == 1:
                    allLeftK += 1
                    left[1].append([m.uid, m.nickName])
                else:
                    continue
        if allLeftK == 0:
            self._reply(msg, TextMsg("耶，今天所有的群员都出完三刀了！"), atReply=True)
            return
        self._reply(msg, TextMsg("PCR报刀插件：当前还剩下{}刀".format(allLeftK)))
        for k, l in left.items():
            if len(l) == 0:
                continue
            if self.memberIsAdmin(msg.bridge, msg.msgInfo.GroupId, msg.msgInfo.UserId) and at:
                self._reply(msg, TextMsg("剩下{}刀({}人):\n".format(k, len(l))))
                atUser = []
                for u in l:
                    atUser.append(u[0])
                if len(atUser) != 0:
                    self._reply(msg, AtMsg(atUser))
            else:
                userName = []
                for u in l:
                    userName.append(u[1])
                if len(userName) != 0:
                    self._reply(msg, TextMsg("剩下{}刀({}人):\n{}".format(
                        k, len(l), '、'.join(userName))))

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
            if g.member.get(myUid) is None:  # 不是本群成员
                continue
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

    def reserve(self, gid, uid, step):
        """
        预约出刀
        """
        try:
            resp = self.pcr.reserve(gid, uid, 0, step)
        except ValueError:
            return TextMsg("不允许预约已经被击破的王")
        if resp:
            return TextMsg("预约成功：将在{}周目{}提醒你哦".format(resp['stage'], str(resp['step']) + "王" if resp['step'] !=
                                                      6 else "5王狂暴"))
        else:
            return TextMsg("预约失败：检查你是否已经预约过了哦")

    def reserveMemberList(self, gid, uid):
        """
        查询指定成员预约记录
        """
        msg = []
        reserveList = self.pcr.reserveMemberList(gid, uid)
        for stage in reserveList.keys():
            strlist = map(lambda i: str(i) + "王" if i !=
                          6 else "5王狂暴", reserveList[stage])
            msg.append("{}周目: {}".format(str(stage),
                                         "、".join(strlist)))
        if len(msg) == 0:
            return [AtMsg(uid), TextMsg("暂无预约记录")]
        else:
            return [AtMsg(uid), TextMsg("的预约记录:\n" + "\n".join(msg))]

    def delReserve(self, gid, uid, stage, step):
        """
        删除指定成员预约记录
        """
        reserve = self.pcr.delReserve(gid, uid, stage, step)
        if not reserve is None:
            return TextMsg("预约的{}王{}周目已被删除".format(reserve.stage, reserve.step))
        else:
            return TextMsg("未找到指定记录")

    def checkReserve(self, msg, cInfo):
        if cInfo.step <= 5 and cInfo.hp == cInfo.fullHP:
            reserveList = self.pcr.reserveStepList(
                msg.msgInfo.GroupId, cInfo.stage, cInfo.step)
            self._reply(msg, [AtMsg(reserveList),
                              TextMsg(
                " 预约的{}周目{}王到了".format(cInfo.stage, cInfo.step))])
        elif cInfo.step == 5 and cInfo.hp <= cInfo.fullHP / 2:  # 半血狂暴
            reserveList = self.pcr.reserveStepList(
                msg.msgInfo.GroupId, cInfo.stage, 6)
            self._reply(msg, [AtMsg(reserveList),
                              TextMsg(
                " 预约的{}周目5王已狂暴".format(cInfo.stage))])

    def run(self):
        self.logger.info("载入 PCR 插件")
        self.redis = Redis(host='127.0.0.1', port=6379,
                           db=0, decode_responses=True)
        self.currentPeriod = "202008"
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


pluginInfo = PCRBOT.PluginInfo()
