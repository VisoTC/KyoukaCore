from . import BaseModel
from peewee import IntegerField, CharField, PrimaryKeyField,BigIntegerField,BooleanField


class Damage(BaseModel):
    id = PrimaryKeyField()
    time = BigIntegerField()
    period = CharField()
    stage = IntegerField()
    step = IntegerField()
    group = IntegerField()
    member = BigIntegerField()
    damage = IntegerField()
    reportDamage = IntegerField()
    kill = BooleanField()

    class Meta:
        db_table = 'damage'
