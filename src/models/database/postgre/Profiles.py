from peewee import CharField
from playhouse.postgres_ext import JSONField

from models.database.postgre.BaseModel import BaseModel


class Profiles(BaseModel):
    unique_id = CharField(primary_key=True, null=False)
    entity_type = CharField(max_length=255)
    profiles = JSONField()
    keywords = JSONField()
    other = JSONField()
