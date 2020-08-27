from enum import unique
from logging import fatal
import re
from typing import Dict, List, Literal

import json
from Class.utli import tz_UTC
from peewee import MySQLDatabase, Ordering, Model
from .ReturnClass import BossInfoReturn, DamageLogListReturn, DamageLogReturn, ReserveReturn
from datetime import datetime, timedelta
from . import orm
from .orm.damage import Damage
from .orm.reserve import Reserve
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
        if not Reserve.table_exists():
            Reserve.create_table()
        self.currentPeriod = currentPeriod

    def changePeriod(self, period):
        self.currentPeriod = period

    def delReserve(self, gid: int, member: int, stage: int, step: int):
        """
        删除预约
        :param gid: 群id
        :param member: 群员id
        :param stage: 预约阶段
        :param step: 预约位置
        """
        try:
            row = Reserve.select().where(Reserve.period == self.currentPeriod,
                                         Reserve.group == gid,
                                         Reserve.member == member,
                                         Reserve.stage == stage,
                                         Reserve.step == step,
                                         ).get()

            row.delete_instance()
            return ReserveReturn(row)
        except Damage.DoesNotExist:
            return None

    def reserveMemberList(self, gid: int, member):
        """
        查询指定成员预约记录, 仅返回未生效的
        :param gid:
        :param member:
        """
        current = self.currentBossInfo(gid)
        if member is None:
            rows = Reserve.select().where(Reserve.period == self.currentPeriod,
                                          Reserve.group == gid,
                                          Reserve.stage >= current.stage)
        else:
            rows = Reserve.select().where(Reserve.period == self.currentPeriod,
                                          Reserve.group == gid,
                                          Reserve.member == member,
                                          Reserve.stage >= current.stage)
        reserveList: Dict[int, List[int]] = {}
        for row in rows:
            if row.stage == current.stage:
                if row.step <= current.step:
                    continue
            if not reserveList.get(row.stage, False):
                reserveList[row.stage] = list()
            reserveList[row.stage].append(row.step)
        return reserveList

    def reserveStepList(self, gid, stage, step):
        """
        返回预约指定阶段的用户列表
        :param stage: 阶段
        :param step: 位置（五王狂暴标记 6）
        """
        rows = Reserve.select().where(Reserve.period == self.currentPeriod,
                                      Reserve.group == gid,
                                      Reserve.stage == stage,
                                      Reserve.step == step)
        memberList = []
        for row in rows:
            memberList.append(row.member)
        return memberList

    def reserve(self, gid: int, member: int, stage: int, step: int):
        """
        预约出刀
        :param gid:
        :param member:
        :param stage: 预约阶段（0为下一个）
        :param step: 预约位置（五王狂暴标记 6）
        :raise ValueError: 尝试预约当前王之前的预约
        """
        current = self.currentBossInfo(gid)
        if stage <= current.stage and stage != 0:
            raise ValueError
        if step <= current.step and stage != 0:
            raise ValueError
        if step <= current.step:
            stage = current.stage + 1
        else:
            stage = current.stage
        # 判断是否重复预约
        reserveList = self.reserveMemberList(gid, member)
        if stage in reserveList.keys():
            if step in reserveList[stage]:
                return False

        row = Reserve(gie=gid,
                      member=member,
                      group=gid,
                      period=self.currentPeriod,
                      stage=stage,
                      step=step,
                      time=int(time.time() * 1000)
                      )
        row.save()
        return {
            "stage": row.stage,
            'step': row.step
        }

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
                                         Damage.group == str(group)
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
                                         Damage.group == str(group)
                                         ).order_by(Damage.time.desc()):
            damageTotal += row.damage
        return BossInfoReturn(
            stage, step, damageTotal, hpIsDamage=True)

    def queryDamageASMember(self, group: int, member: str, date: str = "") -> DamageLogListReturn:
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
        DamageLog = DamageLogListReturn()
        # 连续击杀计数
        ConsecutiveKills = 0
        # 上一刀是否击杀
        nextMakeUp = False
        for row in Damage.select().where(Damage.period == self.currentPeriod,
                                         Damage.group == group,
                                         Damage.member == member,
                                         Damage.time >= queryStartTime,
                                         Damage.time < queryEndTime):
            # 连续击杀计数
            if row.kill:
                ConsecutiveKills += 1
            else:
                ConsecutiveKills = 0
            # 连续击败的奇数刀是尾刀，偶数是补偿尾刀
            if ConsecutiveKills > 0 and ConsecutiveKills % 2 == 0:
                DamageLog.append(DamageLogReturn(
                    row.group, row.member, row.stage, row.step, row.damage, row.kill, row.time, t=3))
                nextMakeUp = False  # 补偿尾刀不需要补偿
            else:
                # 上一刀击杀-补偿刀
                if nextMakeUp:
                    DamageLog.append(DamageLogReturn(
                        row.group, row.member, row.stage, row.step, row.damage, row.kill, row.time, t=2))
                # 上一刀啥都不是
                else:
                    DamageLog.append(DamageLogReturn(
                        row.group, row.member, row.stage, row.step, row.damage, row.kill, row.time, t=0 if not row.kill else 1))  # 击杀了就是尾刀
                nextMakeUp = row.kill  # 本刀击杀下刀补偿
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

    def delLastScore(self, group: int, member: str, allTime=False):
        """
        删除报告的记录：指定对象的指定时间内的最后一条
        :param group: 群 ID
        :param member: 成员
        :param allTime: 范围从五分钟内改为所有时间
        :return: 删除成功：DamageLogReturn, 找不到记录：None
        """
        try:
            if allTime:
                row = Damage.select().where(Damage.period == self.currentPeriod,
                                            Damage.group == group,
                                            Damage.member == member,
                                            ).order_by(Damage.time.desc()).get()
            else:
                row = Damage.select().where(Damage.period == self.currentPeriod,
                                            Damage.group == group,
                                            Damage.member == member,
                                            Damage.time > (int(
                                                time.time()) - (60*5))*1000
                                            ).order_by(Damage.time.desc()).get()
            row.delete_instance()
            return DamageLogReturn(
                row.group, row.member, row.stage, row.step, row.damage, row.kill, row.time)
        except Damage.DoesNotExist:
            return None
