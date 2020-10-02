
from collections import UserDict
from os import kill
from typing import Any, Dict
from typing import List, Optional


import collections

from ..orm.damage import Damage as OrmDamage
from ..bigFunAPI.ret import Damage

from pydantic import BaseModel


class Return(object):
    __readOnlyLock = False

    def readOnlyLock(self):
        self.__readOnlyLock = True

    def __setattr__(self, name: str, value: Any) -> None:
        if self.__readOnlyLock:
            raise AttributeError('{}.{} is READ ONLY'.
                                 format(type(self).__name__, value))
        else:
            return super().__setattr__(name, value)


class BossInfoReturn(Return):
    """
    BOSS 信息
    """

    def __init__(self, stage: int, step: int, hp: int, hpIsDamage=False) -> None:
        """
        :param stage: 周目
        :param step: 位置
        :param hp: 当前血量
        :param hpIsDamage: HP 参数为视作造成的伤害
        """
        self.stage = stage
        self.step = step
        self.fullHP = self.__fillhp()
        if hpIsDamage:
            self.hp = self.fullHP - hp
        else:
            self.hp = hp
        if self.hp <= 0:
            self.step += 1
            if self.step >= 6:
                self.stage += 1
                self.step = 1
            self.fullHP = self.__fillhp()
            self.hp = self.fullHP
        self.readOnlyLock()

    def __fillhp(self):
        if self.step != 5:
            return 1000000 * (2 * self.step + 4)
        if self.step == 5:
            return 1000000 * 20

    def __str__(self):
        return "当前{stage}周目{step}王：{hp}/{fullHP}({percentage:.1%})".format(stage=self.stage, step=self.step, hp=format(self.hp, ','), fullHP=format(self.fullHP, ','), percentage=self.hp/self.fullHP)


class DamageLogReturn(Return):
    def __init__(self, group: int, period: int, playerid: int, stage: int, step: int, damage: int, kill: int, reimburse: int, time: int, score: bool) -> None:
        self.time = time
        self.period = period
        self.stage = stage
        self.step = step
        self.group = group
        self.playerid = playerid
        self.damage = damage
        self.score = score
        self.kill = kill
        self.reimburse = reimburse

    @classmethod
    def ormObj2Self(cls, ormObj: OrmDamage):
        return cls(group=ormObj.group,
                   period=ormObj.period,
                   playerid=ormObj.playerid,
                   stage=ormObj.stage,
                   step=ormObj.step,
                   damage=ormObj.damage,
                   kill=ormObj.kill,
                   reimburse=ormObj.reimburse,
                   time=ormObj.time,
                   score=ormObj.score)

    @classmethod
    def bfAPIDamage2Self(cls, bfAPIDamage: Damage, period: int, group: int, playerid: int):
        return cls(group=group,
                   period=period,
                   playerid=playerid,
                   stage=bfAPIDamage.lapNum,
                   step=bfAPIDamage._step,
                   damage=bfAPIDamage.damage,
                   kill=bfAPIDamage.kill,
                   reimburse=bfAPIDamage.reimburse,
                   time=bfAPIDamage.datetime,
                   score=bfAPIDamage.score)

    def logText(self, name: Optional[str] = None, bossname: Optional[str] = None):
        status = []
        logMsg = "[{status}]{name}对{stage}周目{bossName}造成了{damage}伤害"
        if self.kill:
            logMsg += "并击破"
            status.append("尾刀")
        if self.reimburse:
            status.append('补偿刀')
        if len(status) == 0:
            status.append('正常刀')
        logMsg += "\n得分：%s" % format(self.score, ",")
        return logMsg.format(
            status=",".join(status),
            name=name if name != None else "id: %s" % self.playerid,
            stage=self.stage,
            bossName=bossname +
            "(%s王)" % self.step if bossname != None else "%s王" % self.step,
            damage=format(self.damage, ","))

    def __repr__(self) -> str:
        return self.logText()


class DamageLogListReturn(collections.UserList):
    data: List[DamageLogReturn]

    def getK(self):
        """
        返回剩余刀数
        :return: 总刀数, 完整刀数
        """
        all = 0
        makeUp = 0
        for log in self.data:
            all += 1
            if log.kill == True:  # 尾刀不是完整刀
                makeUp += 1
        return all, all-makeUp


class MappingInfo(collections.UserDict):

    @property
    def mamber(self): return self['mamber']
    @property
    def playerID(self): return self['playerID']
    @property
    def playerName(self): return self['playerName']


class ReserveData(BaseModel):
    id: int
    period: int
    stage: int
    step: int
    group: int
    member: int

    class Config:
        orm_mode = True
