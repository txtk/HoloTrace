from peewee import CharField, UUIDField

from models.database.postgre.BaseModel import BaseModel


class IntrusionSets(BaseModel):
    id = UUIDField(primary_key=True)
    name = CharField(max_length=5000, null=False)
    group = CharField(max_length=255, null=False)
    dataset_type = CharField(max_length=255, null=False)
