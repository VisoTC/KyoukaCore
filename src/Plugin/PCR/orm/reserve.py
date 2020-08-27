from . import BaseModel
from peewee import IntegerField, CharField, PrimaryKeyField,BigIntegerField,BooleanField


class Reserve(BaseModel):
    id = PrimaryKeyField()
    time = BigIntegerField()
    period = CharField()
    stage = IntegerField()
    step = IntegerField()
    group = IntegerField()
    member = BigIntegerField()

    class Meta:
        db_table = 'reserve'
