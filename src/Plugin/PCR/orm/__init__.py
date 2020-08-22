from peewee import Model,MySQLDatabase

db = MySQLDatabase(None)


class BaseModel(Model):

    class Meta:
        database = db
