# 公主连接管理插件 主逻辑
from os import kill
from typing import Any, Dict, List, Optional, Tuple
from peewee import DoesNotExist
import pyqrcodeng
import io
import json
from enum import Enum
from datetime import datetime, timedelta

from Plugin.pcr.cron import NotExecutedx


from .ret import BossInfoReturn, MappingInfo, ReserveData

from .exception import BigFunAPIisLogin, DuplicateNameError, NotFoundPlayerMapping, StepNotFound

from ..bigFunAPI import BigFunAPI, BigFunAPILoginStatus
from ..bigFunAPI.ret import BossInfo, Damage as bfDamage

from .APIAuthInfo import getAuthInfo, setAuthInfo

from ..orm.damage import Damage
from ..orm.bind import Bind
from ..orm.reserve import Reserve
from .ret import DamageLogListReturn, DamageLogReturn
from ..utlis import tz_UTC


class PCR():

    def __init__(self, botUid: int, groupid: int, cookie: Optional[Dict[str, str]] = None) -> None:
        self.gid = groupid
        if cookie == None:
            cookie = getAuthInfo(botUid, self.gid)
        self._bigFunAPI = BigFunAPI(cookie)
        self._battleID = 3
        self.bossList: List[BossInfo] = []

    @property
    def battleID(self):
        return self._battleID

    def setbattleID(self, v):
        self._battleID = v
        self.bossList = self._bigFunAPI.bossList(self.battleID)

    def getAllMappingInfo(self):
        bind = Bind.select().where(Bind.group == self.gid)
        l: List[MappingInfo] = []
        for row in bind:
            l.append(MappingInfo({
                'mamber': row.member,
                'playerID': row.playerID,
                'playerName': row.playerName
            }))
        return l

    def getMappingInfo(self, *, playerID: Optional[int] = None, name: Optional[str] = None, member: Optional[str] = None):
        """
        查询映射表
        """
        try:
            if playerID:
                bind = Bind.get(Bind.group == self.gid,
                                Bind.playerID == playerID)
            elif name:
                bind = Bind.get(Bind.group == self.gid,
                                Bind.playerName == name)
            elif member:
                bind = Bind.get(Bind.group == self.gid,
                                Bind.member == member)
            else:
                raise AttributeError
            return MappingInfo({
                'mamber': bind.member,
                'playerID': bind.playerID,
                'playerName': bind.playerName
            })
        except DoesNotExist:
            raise NotFoundPlayerMapping

    def syncMappingInfo(self):
        """同步映射表"""
        if len(self.bossList) == 0:
            self.bossList = self._bigFunAPI.bossList(self.battleID)
        mapping = self._bigFunAPI.playerIDandPlayerName()
        pidList = []
        name = []
        duplicateName: Optional[Dict[str, List[int]]] = None
        # 判断有没有重名
        for pID in mapping.keys():
            pidList.append(pID)
            if mapping[pID] in name:  # 发现重名
                if duplicateName == None:
                    duplicateName = {}
                try:
                    duplicateName[mapping[pID]].append(pID)
                except KeyError:
                    duplicateName[mapping[pID]] = [pID]

        if duplicateName != None:
            raise DuplicateNameError(duplicateName)

        for pID in pidList:
            bind: Any
            bind, create = Bind.get_or_create(
                group=self.gid, playerID=pID, playerName=mapping[pID])
            if not create:
                if bind.playerName != mapping[pID]:
                    bind.playerName = mapping[pID]
                    bind.save()

    @property
    def apiReady(self):
        return self._bigFunAPI.islogin

    def loginQrcode(self, force=False):
        """
        获得 bigFun 登录二维码
        :param force: 不验证登录状态强行重新登录
        :return: 二维码 png
        """
        if not force:
            if self.apiReady == True:
                raise BigFunAPIisLogin
        qrcodcContent = self._bigFunAPI.login()
        buff = io.BytesIO()
        pyqrcodeng.create(qrcodcContent, error='L',
                          version=5).png(buff, scale=5)
        return buff.getvalue()

    def checkLogin(self):
        """
        判断登录状态
        """
        status = self._bigFunAPI.checklogin()
        if status == BigFunAPILoginStatus.SUCCCESS:  # 登陆成功保存 cookie
            setAuthInfo(self.gid, self._bigFunAPI.cookie2Dict())
        return status

    def userInfo(self):
        '''登录的用户信息'''
        return self._bigFunAPI.userInfo()

    @property
    def playerMapping(self):
        """玩家映射表"""
        return self._bigFunAPI.playerIDandPlayerName()

    def currentBossInfo(self) -> BossInfoReturn:
        '''
        获得当前 BOSS 信息
        :return: 返回当前周目、阶段与剩余血量
        '''
        stage = 1
        step = 1
        damageTotal = 0
        for row in Damage.select().where(Damage.period == self.battleID,
                                         Damage.group == str(self.gid)
                                         ).order_by(Damage.time.desc()):
            if row.stage > stage:
                stage = row.stage
                step = row.step
                damageTotal = 0
            if row.step > step and row.stage == stage:
                step = row.step
                damageTotal = 0
            if row.stage < stage or row.step < step:
                continue
            damageTotal += row.damage
        return BossInfoReturn(
            stage, step, damageTotal, hpIsDamage=True)

    def autoReport(self):
        """
        自动从 BigFun 获取出刀信息并且添加到数据库，并返回添加的列表
        """
        latest, stage, step, logs = self._isDatabaseMatch()
        if latest:  # 没有更新返回新列表
            return logs
        self.syncMappingInfo()
        for log in logs:
            self.reportScore(log)
        return logs

    def _isDatabaseMatch(self):
        """判断数据库与api的数据是否匹配
        :return: 是否匹配，周目，位置，未添加到数据库的列表
        """
        logtime: List[int] = []
        log: Dict[int, bfDamage] = {}
        ret: List[bfDamage] = []
        beforeBossInfo = self.currentBossInfo()
        try:
            lastlog = Damage.select().where(
                Damage.group == self.gid).order_by(Damage.id.desc()).get().time
        except DoesNotExist:
            lastlog = 0
        step = beforeBossInfo.step
        i = 0
        first = True
        while i < 5:
            i += 1
            for row in self._bigFunAPI.allDamageList(self.battleID, self.bossList[step-1].id):
                if row.datetime != None:
                    if row.datetime == lastlog:  # 找到相同的数据
                        if first:
                            return True, row.lapNum, step, ret
                        else:
                            break  # 退出
                    if row.datetime < lastlog:  # 数据比数据库第一条还老
                        break  # 退出
                    row['_step'] = step
                    if not row.datetime in logtime:
                        logtime.append(row.datetime)
                    log[row.datetime] = row
                    first = False
                else:
                    raise Exception
            step += 1
            if step == 6:
                step = 1
        logtime.sort()
        for t in logtime:
            ret.append(log[t])
        return False, 1, 1, ret

    def reportScore(self, damage: bfDamage):
        """报告伤害，建议提前同步映射表"""
        if damage._step == None:
            raise StepNotFound
        Damage(time=damage.datetime,
               period=self.battleID,
               stage=damage.lapNum,
               step=damage._step,
               group=self.gid,
               playerid=self.getMappingInfo(name=damage.name)['playerID'],
               damage=damage.damage,
               score=damage.score,
               kill=damage.kill,
               reimburse=damage.reimburse).save()

    def queryDamageASMember(self, playerid: Optional[int] = None, date: Optional[str] = None):
        '''
        查询成员出刀情况
        :param member: 指定成员(留空代表所有)
        :param date: 日期，样式：20200722
        '''
        # 时间计算
        if date == None:
            today = datetime.now(tz=tz_UTC(8))
            if today.hour < 5:
                today = today - timedelta(hours=5)
            queryStartTime = queryStartTime = datetime(
                today.year, today.month, today.day, 5, 0, 0, tzinfo=tz_UTC(8))
        else:
            queryStartTime = datetime(
                int(date[0:4]), int(date[4:6]), int(date[6:8]), 5, 0, 0, tzinfo=tz_UTC(8))
        queryEndTime = int(
            (queryStartTime + timedelta(days=1)).timestamp())
        queryStartTime = int(queryStartTime.timestamp())
        # 伤害列表
        return self._databaseGetLog(queryStartTime, queryEndTime, playerid)

    def _databaseGetLog(self, startTime: int, endTime: int, playerID: Optional[int] = None):
        '''
        从数据库返回指定范围内的数据
        :param startTime: 开始时间
        :param endTime: 结束时间
        :param playerID: 玩家 ID，默认为全体玩家
        '''
        if playerID == None:
            query = Damage.select().where(Damage.period == self.battleID,
                                          Damage.group == self.gid,
                                          Damage.time >= startTime,
                                          Damage.time < endTime)

        else:
            query = Damage.select().where(Damage.period == self.battleID,
                                          Damage.group == self.gid,
                                          Damage.playerid == playerID,
                                          Damage.time >= startTime,
                                          Damage.time < endTime)
        damageLog: Dict[int, List[DamageLogReturn]] = {}
        for row in query:
            try:
                damageLog[row.playerid].append(
                    DamageLogReturn.ormObj2Self(row))
            except KeyError:
                damageLog[row.playerid] = [DamageLogReturn.ormObj2Self(row)]
        return damageLog

    @staticmethod
    def getK(damageLog: Dict[int, List[DamageLogReturn]]):
        """
        统计log的刀数
        """
        left: Dict[int, Tuple[int, int]] = {}
        for playerid, logs in damageLog.items():
            allK = 0
            completeK = 0
            for log in logs:
                allK += 1
                if log.reimburse or not log.kill:  # 补偿刀或者正常刀都是完整刀
                    completeK += 1
            left[playerid] = allK, completeK
        return left

    @staticmethod
    def leftK(leftLog: Dict[int, Tuple[int, int]]):
        """返回刀数统计信息
        :return: 总刀数，剩余刀数，剩余列表"""
        allK = 90  # 总刀数
        totalK = 0  # 已出刀数
        leftK: Dict[int, int] = {}  # 每个人的剩余刀数
        for playerid, kInfo in leftLog.items():
            leftK[playerid] = 3-kInfo[1] if 3-kInfo[1] >= 0 else 0
            totalK += kInfo[1] if kInfo[1] <= 3 else 3  # 每人最多三刀
        return allK, allK-totalK, leftK

    def rank(self):
        return self._bigFunAPI.rank()

    def bind(self, member, playerid):
        try:
            log = Bind.get(group=self.gid, playerID=playerid)
            if log.member == None:
                log.member = member
                log.save()
                return "ok", str(log.playerName)
            else:
                return "Binded", str(log.playerName)
        except DoesNotExist:
            return "NotFound", None

    def delBind(self, member, playerid, force=False):
        try:
            log = Bind.get(group=self.gid, playerID=playerid, member=member)
            if log.member == member or force:
                log.member = None
                log.save()
                return "ok", str(log.playerName)
            else:
                return "Not Bind You", str(log.playerName)
        except DoesNotExist:
            return "NotFound", None

    def addReserve(self, uid: int, step: int):
        """
        添加一个预约
        """
        if not 1 <= step <= 6:
            raise ValueError
        bossinfo = self.currentBossInfo()
        stage = bossinfo.stage if step >= bossinfo.step else bossinfo.stage + 1
        step = step
        ormObj, isexists = Reserve.get_or_create(period=self.battleID,
                                                 stage=stage,
                                                 step=step,
                                                 member=uid,
                                                 group=self.gid)
        return isexists, ReserveData.from_orm(ormObj)

    def _ORMqueryReserve(self, stage, step, member: Optional[int] = None, latest: Optional[bool] = False):

        if member is None:
            if latest:
                 query = Reserve.select().where(Reserve.period == self.battleID,
                                           Reserve.stage == stage,
                                           Reserve.step == step,
                                           Reserve.group == self.gid)
            else:
                query = Reserve.select().where(Reserve.period == self.battleID,
                                            Reserve.stage == stage,
                                            Reserve.step == step,
                                            Reserve.group == self.gid)
        else:
            query = Reserve.select().where(Reserve.period == self.battleID,
                                           Reserve.stage == stage,
                                           Reserve.step == step,
                                           Reserve.group == self.gid,
                                           Reserve.member == member)
        for row in query:
            row: Reserve
            yield row

    def queryAllReserve(self, member: Optional[int] = None):
        bossInfo = self.currentBossInfo()
        stage = bossInfo.stage
        if member is None:
            query = Reserve.select().where(Reserve.period == self.battleID,
                                           Reserve.stage >= stage,
                                           Reserve.group == self.gid)
        else:
            query = Reserve.select().where(Reserve.period == self.battleID,
                                           Reserve.stage >= stage,
                                           Reserve.group == self.gid,
                                           Reserve.member == member)

        for row in query:
            row: Reserve
            yield row

    def queryReserve(self, stage, step, member: Optional[int] = None):
        """查询指定预约的用户列表"""

        for row in self._ORMqueryReserve(stage, step, member):
            yield ReserveData.from_orm(row)

    def delReserve(self, stage, step, member: Optional[int] = None):
        """删除指定预约的用户列表"""
        emtry = True
        for row in self._ORMqueryReserve(stage, step, member):
            emtry = False
            row.delete_instance()
        if emtry:
            return False
        else:
            return True
