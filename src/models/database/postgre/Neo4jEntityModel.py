from peewee import CharField, UUIDField
from playhouse.postgres_ext import BinaryJSONField


from models.database.postgre.BaseModel import BaseModel

class Neo4jEntityModel(BaseModel):
    id = UUIDField(primary_key=True)
    entity_name = CharField(max_length=5000, null=False)
    entity_type = CharField(max_length=255, null=False)
    data_type = CharField(max_length=255, null=False)
    attributes = BinaryJSONField(null=False)