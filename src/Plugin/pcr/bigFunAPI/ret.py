# 结果类
from typing import Dict, List, Optional, Iterable, Union
import collections



class Damage(collections.UserDict):
    @property
    def datetime(self):
        return self.get('datetime', None)

    @property
    def name(self):
        return self.get('name', None)

    @property
    def lapNum(self):
        return self.get('lap_num', None)

    @property
    def _step(self):
        """需要额外添加，可能不存在"""
        return self.get('_step', None)

    @property
    def kill(self):
        return self.get('kill', None)

    @property
    def reimburse(self):
        return self.get('reimburse', None)

    @property
    def damage(self):
        return self.get('damage', None)

    @property
    def score(self):
        return self.get('score', None)


class DamageList(collections.UserList):

    def __init__(self, initlist: Optional[Iterable[Union[Dict, Damage]]] = None) -> None:
        super().__init__()
        for i in initlist:
            if not isinstance(i, Damage):
                self.data.append(Damage(i))
            else:
                self.data.append(i)


class UserInfo(collections.UserDict):
    @property
    def arenaHighestRank(self):
        """竞技场最高排名"""
        return self.get('arena_highest_rank', None)

    @property
    def arenaRank(self):
        """竞技场当前排名"""
        return self.get('arena_rank', None)

    @property
    def clanName(self):
        """公会名"""
        return self.get('clan_name', None)

    @property
    def clanRole(self):
        """工会职务"""
        return self.get('clan_role', None)

    @property
    def grandArenaHighestRank(self):
        """公主竞技场最高排名"""
        return self.get('grand_arena_highest_rank', None)

    @property
    def grandArenaRank(self):
        """公主竞技场当前排名"""
        return self.get('grand_arena_rank', None)

    @property
    def hardQuest(self):
        """完成的困难任务数量"""
        return self.get('hard_quest', None)

    @property
    def normalQuest(self):
        """完成的普通任务数量"""
        return self.get('normal_quest', None)

    @property
    def playerID(self):
        """玩家 ID"""
        return self.get('player_id', None)

    @property
    def playerLevel(self):
        """玩家等级"""
        return self.get('player_level', None)

    @property
    def playerName(self):
        """玩家名"""
        return self.get('player_name', None)

    @property
    def totalPower(self):
        """总战力"""
        return self.get('total_power', None)


class BossInfo(collections.UserDict):
    @property
    def id(self):
        return self.get('id', None)

    @property
    def name(self):
        return self.get('boss_name', None)

class TeamInfo(collections.UserDict):
    @property
    def clanName(self):
        return self.get('clan_name', None)

    @property
    def damage(self):
        return self.get('damage', None)
    
    @property
    def leaderName(self):
        return self.get('clan_name', None)

    @property
    def rank(self):
        return self.get('rank', None)