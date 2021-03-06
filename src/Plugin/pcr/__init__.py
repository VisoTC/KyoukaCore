import json
from typing import Any, Callable, Dict, List, Optional, Text, Tuple
import os
import time

from Core.Service.Plugin import PluginService, ServiceInfo
from Core.Event.MsgEvent.MsgInfo import GroupMsgInfo, PrivateMsgInfo
from Core.Event.MsgEvent.MsgContent import AtMsg, MsgContent, PicMsg, TextMsg
from Core.Event.MsgEvent import MsgEvent
from Core.Event import Eventer, ReceiveEvent, ServiceType
from Core.Service.Command import Command
from Core.Service.exception import NotFoundGroup

from .bigFunAPI import ret
from .bigFunAPI.ret import TeamInfo
from .pcr.exception import BigFunAPIisLogin, NotFoundPlayerMapping
from .pcr import PCR
from .bigFunAPI import BigFunAPI, BigFunAPILoginStatus
from .orm import db
from .orm.damage import Damage
from .orm.reserve import Reserve
from .orm.apiAuthInfo import APIAuthInfo
from .orm.bind import Bind
from .utlis import tz_UTC
from .pcr.ret import DamageLogReturn, ReserveData

from .cron import Cron, CronManager, RemoveCron

pcrPlugin = PluginService(ServiceInfo(**{
    'packageName': "com.visotc.KyoukaCore.PCR",
    'name': "公主连结插件",
    'version': "1",
    'author': "VisoTC"
}))
debug = False
pcrPlugin.context['Groups'] = {}

cronManager = CronManager()


@pcrPlugin.register("register")
def main(unuse):
    if debug:
        db.init(':memory:')
    else:
        dbPath = os.path.join(os.path.split(
            os.path.realpath(__file__))[0], "database")
        if not os.path.exists(dbPath):
            os.mkdir(dbPath)
        dbName = 'pcr.db'
        db.init(os.path.join(dbPath, dbName))
    db.connect()
    # 创建表
    if not Damage.table_exists():
        Damage.create_table()
    if not Reserve.table_exists():
        Reserve.create_table()
    if not APIAuthInfo.table_exists():
        APIAuthInfo.create_table()
    if not Bind.table_exists():
        Bind.create_table()
    # 注册 api
    for group in APIAuthInfo.select():
        pcr = PCR(group.botUid, group.gid, json.loads(group.cookie))
        addPCR(group.botUid, group.gid, pcr)
    #cronManager.append(Cron(60*1, cronAutoReport))
    #cronManager.append(Cron(60*30, cronRank))
    cronManager.start()


def addPCR(botUid, gid, pcr):
    if pcr.apiReady:
        try:
            pcrPlugin.context['Groups'][botUid][gid] = pcr
        except KeyError:
            pcrPlugin.context['Groups'][botUid] = {gid: pcr}
    else:
        pcrPlugin.logger.error("与群 {} 绑定的 API 还未就绪".format(str(pcr.gid)))


def cronRank(data):
    if len(data) == 0:
        data.append(0)
        return
    for botuid in pcrPlugin.context['Groups'].keys():
        for gid in pcrPlugin.context['Groups'][botuid].keys():
            pcr: PCR = pcrPlugin.context['Groups'][botuid][gid]
            rankInfo = pcr.rank()
            if isinstance(rankInfo, TeamInfo):
                pcrPlugin.api.sendMsg(Eventer(botuid, ServiceType.Bridge), MsgEvent(GroupMsgInfo(gid), TextMsg(
                    "公会:{}\n当前排名：{} 总分：{}".format(rankInfo.clanName, rankInfo.rank, format(rankInfo.damage, ",")))))


def cronAutoReport(data):
    for botuid in pcrPlugin.context['Groups'].keys():
        for gid in pcrPlugin.context['Groups'][botuid].keys():
            autoReport(
                botuid, gid, pcrPlugin.context['Groups'][botuid][gid])


def autoReport(botuid, gid, pcr: PCR):
    '''自动从 Bigfun 拉取出刀数据'''
    pcr.syncMappingInfo()  # 同步公会名称数据
    isNewData = False
    lastBossInfo = pcr.currentBossInfo()
    for newlog in pcr.autoReport():  # 同步出刀数据并返回新记录
        isNewData = True
        playerMapping = pcr.getMappingInfo(name=newlog.name)
        msg: List[MsgContent] = []
        member: Optional[str] = playerMapping.mamber
        if member != None:
            msg.append(AtMsg(int(member)))
        else:
            msg.append(TextMsg('*此玩家还未绑定*'))
        msg.append(TextMsg("\n" + DamageLogReturn.bfAPIDamage2Self(
            newlog,
            period=pcr.battleID,
            group=pcr.gid,
            playerid=playerMapping.playerID
        ).logText(name=playerMapping.playerName, bossname=pcr.bossList[newlog._step - 1].name)))

        pcrPlugin.api.sendMsg(
            Eventer(botuid, ServiceType.Bridge), MsgEvent(GroupMsgInfo(gid), msg))
    if isNewData:
        newBossInfo = pcr.currentBossInfo()
        pcrPlugin.api.sendMsg(Eventer(botuid, ServiceType.Bridge), MsgEvent(
            GroupMsgInfo(gid), TextMsg(str(newBossInfo))))
        step = newBossInfo.step
        if lastBossInfo.step != newBossInfo.step:
            query = pcr.queryReserve(newBossInfo.stage, newBossInfo.step)
        elif newBossInfo.step == 5 and newBossInfo.hp >= 10000000 and lastBossInfo.hp < 10000000:
            step = 6
            query = pcr.queryReserve(newBossInfo.stage, step)
        else:
            return
        nofiyId = []
        for row in query:
            nofiyId.append(row.member)
        pcrPlugin.api.sendMsg(Eventer(botuid, ServiceType.Bridge), MsgEvent(
            GroupMsgInfo(gid), [TextMsg('你预约的{}到了'.format(_ReserveBossID2Name(step,pcr))), AtMsg(nofiyId)]))


def _ReserveBossID2Name(i,pcr:Optional[PCR] = None):
    if pcr is None:
        return "{}王".format(i) if i < 6 else "5王狂暴"
    else:
        return "{}({}王)".format(pcr.bossList[(i if i < 6 else 5) - 1].name,i if i < 6 else 5) 


def _getPCRObj(event: ReceiveEvent[MsgEvent]) -> PCR:
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        try:
            return pcrPlugin.context['Groups'][int(event.source.name)][event.payload.msgInfo.GroupId]
        except KeyError as e:
            pcrPlugin.api.reply(event, TextMsg("本群还未注册，不支持此功能"))
            raise e
    else:
        pcrPlugin.api.reply(event, TextMsg("此功能只支持群聊哦"))
        raise KeyError


def bossinfo(event: ReceiveEvent[MsgEvent]):
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        pcr = _getPCRObj(event)
        pcrPlugin.api.reply(event, TextMsg(str(pcr.currentBossInfo())))


def syncNow(event: ReceiveEvent[MsgEvent]):
    '''立即更新，需要群管理员'''
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        pcr = _getPCRObj(event)
        if pcrPlugin.api.isGroupAdmin(event.source, event.payload.msgInfo.GroupId, event.payload.msgInfo.UserId):
            autoReport(event.source.name, event.payload.msgInfo.GroupId, pcr)
            pcrPlugin.api.reply(event, TextMsg("已完成同步"))
        else:
            pcrPlugin.api.reply(event, TextMsg("需要是群管理员才可以调用此功能哦"))


def _getAtList(event: ReceiveEvent[MsgEvent], default: str) -> Tuple[List[str], bool]:
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        atMsg: Optional[AtMsg] = None
        for m in event.payload.msgContent:
            if isinstance(m, AtMsg):
                if atMsg is None:
                    atMsg = m
                else:
                    pcrPlugin.logger.warn("重复消息链，抛弃")
        if atMsg == None:
            user = [default], False
        else:
            user = atMsg.atUser[0], True
        return user
    else:
        return [default], False


def queryDamage(event: ReceiveEvent[MsgEvent]):
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        user, isAtUser = _getAtList(event, event.payload.msgInfo.UserId)
        if isAtUser:
            if not pcrPlugin.api.isGroupAdmin(event.source, event.payload.msgInfo.GroupId, event.payload.msgInfo.UserId):
                pcrPlugin.api.reply(event, TextMsg("需要是管理员才可以查询其他人的出刀记录哦"))
                return
        if len(user) != 1:
            pcrPlugin.api.reply(event, TextMsg(
                "只能@一个人哦，而你@了%s个" % len(user)))
            return
        pcr = _getPCRObj(event)
        try:
            mapping = pcr.getMappingInfo(member=user[0])
        except NotFoundPlayerMapping:
            pcrPlugin.api.reply(event, TextMsg(
                "{}还没有绑定游戏账户哦".format("你" if user[0] == event.payload.msgInfo.UserId else "该玩家")))
            return
        playerid = mapping['playerID']
        logs = pcr.queryDamageASMember(playerid)
        try:
            logMsg = ["今日已出{}刀（完整刀{}刀）".format(*pcr.getK(logs)[playerid])]
        except KeyError:
            pcrPlugin.api.reply(event, TextMsg(
                "玩家：{} 今日还没有出刀记录哦".format(mapping.playerName)))
            return
        logMsg.extend([log.logText(name=mapping['playerName'],
                                   bossname=pcr.bossList[log.step-1]['boss_name'])
                       for log in logs[playerid]])
        pcrPlugin.api.reply(event, TextMsg('\n'.join(logMsg)))


def urge(event: ReceiveEvent[MsgEvent]):
    """催刀"""
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        pcr = _getPCRObj(event)
        u = _queryK(pcr, False)
        if u != None:
            pcrPlugin.api.reply(event, [TextMsg("当前还剩下{}刀".format(u[0][0]))])
            if(u[0][0] == 0):
                pcrPlugin.api.reply(event, [TextMsg("恭喜出刀完成！")])
            for left, lis in u.items():
                if len(lis) == 0:
                    continue
                if left == 0:
                    continue
                notBind = []
                atlist = []
                for playerID in lis:
                    mapping = pcr.getMappingInfo(playerID=playerID)
                    if mapping.mamber == None:
                        notBind.append(mapping.playerName)
                    else:
                        atlist.append(mapping.mamber)
                pcrPlugin.api.reply(event, TextMsg("剩余{}刀".format(left)))
                if len(notBind) != 0:
                    pcrPlugin.api.reply(event, TextMsg(
                        "未绑定的玩家：{}".format('、'.join(notBind))))
                if len(atlist) != 0:
                    pcrPlugin.api.reply(event, AtMsg(atlist))


def left(event: ReceiveEvent[MsgEvent]):
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        pcr = _getPCRObj(event)
        u = _queryK(pcr, True)
        if u != None:
            pcrPlugin.api.reply(event, [TextMsg("当前还剩下{}刀".format(u[0][0]))])
            if(u[0][0] == 0):
                pcrPlugin.api.reply(event, [TextMsg("恭喜出刀完成！")])
            for left, lis in u.items():
                if len(lis) == 0:
                    continue
                if left == 0:
                    continue
                pcrPlugin.api.reply(event, TextMsg("剩余{}刀".format(left)))
                pcrPlugin.api.reply(event, TextMsg('、'.join(lis)))


def _queryK(pcr: PCR, returnPlayerName=False):
    logs = pcr.queryDamageASMember()
    klog = pcr.getK(logs)
    lefts = {
        3: [],
        2: [],
        1: [],
        0: []
    }
    allLeft = 0
    empty = True
    for mapping in pcr.getAllMappingInfo():
        empty = False
        try:
            _, complete = klog[mapping.playerID]
        except KeyError:
            complete = 0
        left = 3 - complete
        allLeft += left if left > 0 else 0
        if left > 0:
            if returnPlayerName:
                lefts[left].append(mapping.playerName)
            else:
                lefts[left].append(mapping.playerID)
    lefts[0].append(allLeft)
    if empty:
        return None
    else:
        return lefts


def login(event: ReceiveEvent[MsgEvent], gid):
    if isinstance(event.payload.msgInfo, PrivateMsgInfo):
        try:
            if not pcrPlugin.api.getGroupsList(event.source).get(gid).member.get(event.payload.msgInfo.UserId).isAdmin:
                pcrPlugin.api.reply(event, TextMsg("你需要是该群的管理员才可以执行这个操作哦"))
                return
        except NotFoundGroup:
            pcrPlugin.api.reply(event, TextMsg("我还没有加入这个群哦"))
            return
        pcr = PCR(int(event.source.name), gid)
        try:
            pcrPlugin.api.reply(
                event, [PicMsg(pcr.loginQrcode()), TextMsg("请使用 bilibili 扫码登录")])
        except BigFunAPIisLogin:
            pcrPlugin.api.reply(event, TextMsg("该群已登录 BigFun"))
            return
        cronManager.append(
            Cron(1, checklogin, [pcr, event, BigFunAPILoginStatus.WAITSCAN, 0]))


def checklogin(data: List[Any]):
    event: ReceiveEvent[MsgEvent] = data[1]
    lastStatus: BigFunAPILoginStatus = data[2]
    if data[3] >= 60:
        pcrPlugin.api.reply(event, TextMsg("由于登录超时，系统已取消当前登录操作"))
    pcr: PCR = data[0]
    data[3] += 1
    status = pcr.checkLogin()
    if lastStatus != status:
        if status == BigFunAPILoginStatus.SCANED:
            msg = "已扫码，等待确认"
            pcrPlugin.api.reply(data[1], TextMsg(msg))
        elif status == BigFunAPILoginStatus.SUCCCESS:
            info = pcr.userInfo()
            msg = "登陆成功！\n当前用户：{}\n所在公会：{}\n即将开始同步战斗数据".format(
                info.playerName, info.clanName)
            pcrPlugin.api.reply(data[1], TextMsg(msg))
            addPCR(event.source.name, pcr.gid, pcr)
            pcr.syncMappingInfo()
            log = pcr.autoReport()
            msg = "公会：{}同步完成，已同步{}条数据\n{}".format(
                info.clanName, len(log), str(pcr.currentBossInfo()))
            pcrPlugin.api.reply(event, TextMsg(msg))
            pcrPlugin.api.sendMsg(event.source, MsgEvent(
                GroupMsgInfo(pcr.gid), TextMsg(msg)))
            raise RemoveCron
        elif status == BigFunAPILoginStatus.NOT_CALL_LOGIN:
            msg = "二维码已失效，请重新扫码"
            pcrPlugin.api.reply(data[1], TextMsg(msg))
            raise RemoveCron
        elif status == BigFunAPILoginStatus.FAILER:
            msg = "登陆失败"
            pcrPlugin.api.reply(data[1], TextMsg(msg))
            raise RemoveCron
    data[2] = status


def bindPlayer(event: ReceiveEvent[MsgEvent], playerID: int):
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        pcr = _getPCRObj(event)
        status, name = pcr.bind(event.payload.msgInfo.UserId, playerID)
        if status == "ok":
            pcrPlugin.api.reply(event, TextMsg(
                '成功与游戏名为：{} 的账户绑定'.format(name)))
        elif status == "Binded":
            pcrPlugin.api.reply(event, TextMsg('游戏名为：{} 的账户已被绑定'.format(name)))
        else:
            pcrPlugin.api.reply(event, TextMsg('在公会内找不到此用户'))


def delBindPlayer(event: ReceiveEvent[MsgEvent], playerID: int):
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        user, isAtUser = _getAtList(event, event.payload.msgInfo.UserId)
        if isAtUser:
            if not pcrPlugin.api.isGroupAdmin(event.source, event.payload.msgInfo.GroupId, event.payload.msgInfo.UserId):
                pcrPlugin.api.reply(event, TextMsg("需要是管理员才可以解除其他人的绑定哦"))
                return
        if len(user) != 1:
            pcrPlugin.api.reply(event, TextMsg(
                "只能@一个人哦，而你@了%s个" % len(user)))
            return
        pcr = _getPCRObj(event)
        status, name = pcr.delBind(user[0], playerID,
                                   force=pcrPlugin.api.eventUserIsGroupAdmin(event) and isAtUser)
        if status == "ok":
            pcrPlugin.api.reply(event, TextMsg(
                '成功与游戏名为：{} 的账户解绑'.format(name)))
        elif status == "Not Bind You":
            pcrPlugin.api.reply(event, TextMsg(
                '游戏名为：{} 的账户绑定的不是你'.format(name)))
        else:
            pcrPlugin.api.reply(event, TextMsg('在公会内找不到此用户'))


def rank(event: ReceiveEvent[MsgEvent]):
    pcr: PCR = _getPCRObj(event)
    rankInfo = pcr.rank()
    if isinstance(rankInfo, TeamInfo):
        pcrPlugin.api.reply(event, TextMsg(
            "公会:{}\n当前排名：{} 总分：{}".format(rankInfo.clanName, rankInfo.rank, format(rankInfo.damage, ","))))

# -------------
#   预约系统
# -------------


def addReserve(event: ReceiveEvent[MsgEvent], step: str):
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        notdigitMsg = "请输入 1-6 之间的阿拉伯数字\nP.S.: 6 代表 5 王狂暴"
        if not step.isdigit():
            pcrPlugin.api.reply(event, TextMsg(notdigitMsg))
            return
        pcr = _getPCRObj(event)
        try:
            pcr.getMappingInfo(member=event.payload.msgInfo.UserId)
        except NotFoundPlayerMapping:
            pcrPlugin.api.reply(event, TextMsg("尚未绑定账户，暂时无法使用此功能"))
            return
        try:
            status, row = pcr.addReserve(
                event.payload.msgInfo.UserId, int(step))
        except ValueError:
            pcrPlugin.api.reply(event, TextMsg(notdigitMsg))
            return
        if status:
            pcrPlugin.api.reply(event, TextMsg("已预约{}周目{}".format(
                row.stage,_ReserveBossID2Name(row.step,pcr))))
        else:
            pcrPlugin.api.reply(event, TextMsg("你已经预约了{}周目{}".format(
                row.stage, _ReserveBossID2Name(row.step,pcr))))


def delReserve(event: ReceiveEvent[MsgEvent], stage: str, step: str):
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        notdigitMsg = "请输入 1-6 之间的阿拉伯数字\nP.S.: 6 代表 5 王狂暴"
        if not stage.isdigit():
            pcrPlugin.api.reply(event, TextMsg("第一个参数需要输入阿拉伯数字哦"))
            return
        if not step.isdigit():
            pcrPlugin.api.reply(event, TextMsg(notdigitMsg))
            return
        pcr = _getPCRObj(event)
        status = pcr.delReserve(
            stage, step, member=event.payload.msgInfo.UserId)
        if status:
            pcrPlugin.api.reply(event, TextMsg("已取消预约{}周目{}".format(
                stage, _ReserveBossID2Name(step,pcr))))
        else:
            pcrPlugin.api.reply(event, TextMsg("在预约列表找不到此预约"))


def queryReserve(event: ReceiveEvent[MsgEvent]):
    if isinstance(event.payload.msgInfo, GroupMsgInfo):
        pcr = _getPCRObj(event)
        user, isAtUser = _getAtList(event, event.payload.msgInfo.UserId)
        if isAtUser:
            if not pcrPlugin.api.isGroupAdmin(event.source, event.payload.msgInfo.GroupId, event.payload.msgInfo.UserId):
                pcrPlugin.api.reply(event, TextMsg("需要是管理员才可以查询其他人的出刀记录哦"))
                return
        if len(user) != 1:
            pcrPlugin.api.reply(event, TextMsg(
                "只能@一个人哦，而你@了%s个" % len(user)))
            return
        else:
            user = user[0]
        reserveList: List[str] = []
        for row in pcr.queryAllReserve(member=int(user)):
            reserveList.append(
                " - {}周目{}".format(row.stage, _ReserveBossID2Name(row.step,pcr)))

        if len(reserveList) != 0:
            pcrPlugin.api.reply(event, TextMsg(
                "预约列表\n{}".format("\n".join(reserveList))))
        else:
            pcrPlugin.api.reply(event, TextMsg("无预约"))


def initCommand():
    cSync = Command("sync", "【管理员】立即同步数据", GroupMsgInfo, func=syncNow)
    cQuery = Command('查刀', '查询出刀情况', GroupMsgInfo, func=queryDamage)
    cUrge = Command('催刀', 'at 没有出刀的人', GroupMsgInfo, func=urge)
    cLeft = Command('剩刀', '查看没有出刀的人', GroupMsgInfo, func=left)
    cBossinfo = Command('boss', "当前 BOSS 剩余血量", GroupMsgInfo, func=bossinfo)
    cBind = Command('bind', "与游戏内用户绑定", GroupMsgInfo, func=bindPlayer)
    cDelBind = Command('delbind', "与游戏内用户解除绑定",
                       GroupMsgInfo, func=delBindPlayer)
    cRank = Command('rank', "查看当前排名", GroupMsgInfo, func=rank)

    cAddServe = Command('预约', "等到了指定boss提醒你", GroupMsgInfo, func=addReserve)
    cDelServe = Command('鸽子', "鸽掉某个预约", GroupMsgInfo, func=delReserve)
    cqueryServe = Command('查预约', "查询预约情况",
                          GroupMsgInfo, func=queryReserve)

    cLogin = Command('apibind', "绑定 api 账户", PrivateMsgInfo, func=login)
    rootCommand = Command("pcr", "PCR 公会管理协助插件", None,
                          sub=[cSync, cQuery, cUrge, cLogin, cBossinfo, cBind, cLeft, cRank, cDelBind, cAddServe, cDelServe, cqueryServe])
    pcrPlugin.registerCommand(rootCommand)

    pcrPlugin.initDone(True)


initCommand()
