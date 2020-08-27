from collections import UserList
import re
from Class.utli import tz_UTC
from datetime import datetime
from typing import List, Dict
import typing


class Return(object):
    __readOnlyLock = False

    def readOnlyLock(self):
        self.__readOnlyLock = True

    def __setattr__(self, name: str, value: any) -> None:
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
    """伤害日志"""

    def __init__(self, group: int, member: str, stage: int, step: int, damage: int, kill: int, time: int, t: int=-1) -> None:
        """
        :param group: 成员
        :param member: 成员
        :param stage: 周目
        :param step: 位置
        :param damage: 造成的伤害
        :param kill: 是否击破
        :param time: 记录时间
        :param t: 刀类型：0-正常；1-尾刀；2-补偿刀；3-补偿刀,尾刀
        """
        self.group = group
        self.member = member
        self.stage = stage
        self.step = step
        self.damage = damage
        self.kill = kill
        self.time = time
        self.t = t
        self.readOnlyLock()

    @property
    def KType(self):
        if self.t == 0:
            return '正常刀'
        elif self.t == 1:
            return '尾刀'
        elif self.t == 2:
            return '补偿刀'
        elif self.t == 3:
            return '补偿刀,尾刀'
        else:
            return '类型: %s' % str(self.t)

    @property
    def timeStr(self):
        return datetime.fromtimestamp(
            self.time/1000, tz=tz_UTC(8)).strftime("%Y年%m月%d日%H:%M:%S")

    def __str__(self):
        if self.kill != 0:
            msg = "{member}于{time}对{stage}周目{step}王造成了{damage}伤害并击败"
        else:
            msg = "{member}于{time}对{stage}周目{step}王造成了{damage}伤害"
        return msg.format(member=self.member, time=self.timeStr, stage=self.stage, step=self.step, damage=self.damage)


class DamageLogListReturn(UserList):
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
            if log.t == 1: # 尾刀不是完整刀
                makeUp += 1
        return all, all-makeUp


class ReportScoreReturn(Return):
    def __init__(self, member: str, damage: int, stage: int, step: int, hp: int) -> None:

        self.readOnlyLock()

    def __init__(self, member: str, damage: int, bossInfoReturn: BossInfoReturn) -> None:
        return self.__init__(member, damage, bossInfoReturn.stage, bossInfoReturn.step, bossInfoReturn.hp)

class ReserveReturn(Return):
    def __init__(self,reserveORM) -> None:
        self.id = reserveORM.id
        self.time = reserveORM.time
        self.period = reserveORM.period
        self.stage = reserveORM.stage
        self.step = reserveORM.step
        self.group = reserveORM.group
        self.member = reserveORM.member
        self.readOnlyLock()