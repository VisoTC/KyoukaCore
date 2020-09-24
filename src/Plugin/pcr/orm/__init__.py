from peewee import Model,SqliteDatabase

db = SqliteDatabase(None)

__all__=['db']
class BaseModel(Model):

    class Meta:
        database = db