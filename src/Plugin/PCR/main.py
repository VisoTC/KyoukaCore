from logging import fatal
import re
from typing import Dict, List, Literal

import json
from Class.utli import tz_UTC
from peewee import MySQLDatabase, Ordering,Model
from .ReturnClass import BossInfoReturn, DamageLogReturn
from datetime import datetime, timedelta
from . import orm
from .orm.damage import Damage
import time


class PCR(object):

    def __init__(self, dataBase, currentPeriod: str) -> None:
        """
        :param dataBase: 数据库信息，传入 Dict:{
            'database':"",
            'host':'',
            'port':0,
            'user':'',
            'passwd':''
        }
        :param currentPeriod: 指示当前阶段
        """
        orm.db.init(**dataBase)
        orm.db.connect()
        if not Damage.table_exists():
            Damage.create_table()
        self.currentPeriod = currentPeriod

    def changePeriod(self, period):
        self.currentPeriod = period

    def currentBossInfo(self, group: int) -> BossInfoReturn:
        '''
        获得当前 BOSS 信息
        :param group: 群 ID
        :return: 返回当前周目、阶段与剩余血量
        '''

        stage = 1
        step = 1
        damageTotal = 0
        for row in Damage.select().where(Damage.period == self.currentPeriod,
                                         Damage.group == str(group)).order_by(Damage.time.desc()):
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

    def BossInfo(self, group: int, stage, step) -> BossInfoReturn:
        '''
        获得指定周目的 BOSS 信息
        :param group: 群 ID
        :param stage: 强制设定当前周目
        :param step: 强制设定当前位置
        :return: 返回当前周目、阶段与剩余血量
        '''
        damageTotal = 0
        for row in Damage.select().where(Damage.period == self.currentPeriod,
                                         Damage.stage == stage,
                                         Damage.step == step,
                                         Damage.group == str(group)).order_by(Damage.time.desc()):
            damageTotal += row.damage
        return BossInfoReturn(
            stage, step, damageTotal, hpIsDamage=True)

    def queryDamageASMember(self, group: int, member: str, date: str = "") -> List[DamageLogReturn]:
        '''
        查询成员出刀情况
        :param group: 群 ID
        :param member:  指定成员
        :param date: 日期，样式：20200722
        '''
        if date == "":
            today = datetime.now(tz=tz_UTC(8))
            if today.hour < 5:
                today = today - timedelta(hours=5)
            queryStartTime = queryStartTime = datetime(
                today.year, today.month, today.day, 5, 0, 0, tzinfo=tz_UTC(8))
        else:
            queryStartTime = datetime(
                int(date[0:4]), int(date[4:6]), int(date[6:8]), 5, 0, 0, tzinfo=tz_UTC(8))
        queryEndTime = int(
            (queryStartTime + timedelta(days=1)).timestamp() * 1000)
        queryStartTime = int(queryStartTime.timestamp()*1000)
        DamageLog: List[DamageLogReturn] = []

        for row in Damage.select().where(Damage.period == self.currentPeriod,
                                         Damage.group == group,
                                         Damage.member == member,
                                         Damage.time >= queryStartTime,
                                         Damage.time < queryEndTime):
            DamageLog.append(DamageLogReturn(
                row.group, row.member, row.stage, row.step, row.damage, row.kill, row.time))
        return DamageLog

    def reportScore(self, group: int, member: str, damage: int, stage: int = None, step: int = None) -> None:
        '''
        对当前 BOSS 造成的伤害量
        :param group: 群 ID
        :param member: 成员
        :param damage: 造成的伤害
        :param stage: 【可选】强制设定当前周目
        :param step: 【可选】强制设定当前位置
        '''
        kill = False
        if stage != None or step != None:  # 补报刀
            if not (stage != None and step != None):   # 必须同时输入
                raise ValueError
            beforeBOSSInfo = self.BossInfo(
                group, stage, step)  # 获得指定位置的 BOSS 信息
        else:
            beforeBOSSInfo = self.currentBossInfo(group)
        if beforeBOSSInfo.hp - damage <= 0:  # 击破
            trueDamage = beforeBOSSInfo.hp
            kill = True
        else:
            trueDamage = damage

        Damage(time=int(time.time() * 1000),  # 储存毫秒
               period=self.currentPeriod,
               stage=beforeBOSSInfo.stage if stage is None else stage,
               step=beforeBOSSInfo.step if step is None else step,
               group=group,
               member=member,
               reportDamage=damage,
               damage=trueDamage,
               kill=kill).save()
        if stage != None and step != None:  # 必须同时输入
            currentBOSSInfo = self.BossInfo(group, stage, step)
        else:
            currentBOSSInfo = self.currentBossInfo(group)
        return currentBOSSInfo, kill

    def delLastScore(self, group: int, member: str):
        """
        删除报告的记录：指定对象的指定时间内的最后一条
        :param group: 群 ID
        :param member: 成员
        :return: 删除成功：DamageLogReturn, 找不到记录：None
        """
        try:
            row = Damage.select().where(Damage.period == self.currentPeriod,
                                      Damage.group == group,
                                      Damage.member == member,
                                      Damage.time > (int(
                                          time.time())- (60*5))*1000
                                      ).order_by(Damage.time.desc()).get()
            row.delete_instance()
            return DamageLogReturn(
                row.group, row.member, row.stage, row.step, row.damage, row.kill, row.time)
        except Damage.DoesNotExist:
            return None
