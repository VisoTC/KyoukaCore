from . import BaseModel
from peewee import IntegerField, CharField, PrimaryKeyField, BigIntegerField, BooleanField


class Damage(BaseModel):
    id = PrimaryKeyField()
    time = BigIntegerField(help_text="时间")
    period = CharField(help_text="期数")
    stage = IntegerField(help_text="周目")
    step = IntegerField(help_text="BOSS 位置")
    group = IntegerField(help_text="群 id")
    playerid = BigIntegerField(help_text="游戏 id")
    damage = IntegerField(help_text="伤害")
    score = IntegerField(help_text="得分")
    kill = BooleanField(help_text="是否击败")
    reimburse = BooleanField(help_text="是否补偿刀")

    class Meta:
        db_table = 'damage'
